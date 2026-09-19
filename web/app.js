"use strict";
/* AlphaVoice web simulation: a thin browser client over the real MCP server.
 * Plain JS, no build step, no frameworks. The only network calls this file
 * makes are POSTs to http://localhost:8000/mcp (MCP Streamable HTTP).
 *
 * What is simulated: the agent routing (keyword match, labeled in the UI).
 * What is real: the tool call itself, over JSON-RPC to the MCP server.
 */

const MCP_URL = "http://localhost:8000/mcp";
/* The server README targets MCP spec 2025-11-25; older versions are tried as fallback. */
const PROTOCOL_VERSIONS = ["2025-11-25", "2025-06-18", "2024-11-05"];
const CLIENT_INFO = { name: "alphavoice-web", version: "0.1.0" };
const REQUEST_TIMEOUT_MS = 12000;
const TOOL_NAMES = ["market_brief", "signal_scan", "mispricing_check", "news_microstructure"];

/* Simulated routing table. Keyword based, labeled as simulated in the UI. */
const ROUTES = [
  {
    tool: "market_brief",
    keywords: ["morning brief", "brief", "full picture", "everything today", "all three", "roundup"],
    topic: "the composed multi-tool morning brief",
  },
  {
    tool: "news_microstructure",
    keywords: ["cpi", "inflation", "fed", "news", "print", "absorb", "absorbed", "absorption",
               "headline", "release", "announcement", "macro", "earnings"],
    topic: "news absorption speed",
  },
  {
    tool: "mispricing_check",
    keywords: ["mispric", "polymarket", "kalshi", "arbitrage", "spread", "rich to", "cheap to",
               "price gap", "cross-market", "election market", "paper position"],
    topic: "cross-market mispricing",
  },
  {
    tool: "signal_scan",
    keywords: ["momentum", "mean-reversion", "mean reversion", "reversion", "signal",
               "unusual", "scan", "movers", "trade idea", "ranking", "today"],
    topic: "momentum and mean-reversion signals",
  },
];

const session = { sessionId: null, protocolVersion: null, tools: null, ready: false };
const state = { busy: false, speakingUntil: 0 };
let rpcId = 1;

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/* ---- MCP Streamable HTTP client --------------------------------------- */

/* Parse a Streamable HTTP response body that arrived as server-sent events.
 * Returns the last complete JSON-RPC message found in data: lines. */
function parseSseMessage(text) {
  let last = null;
  for (const raw of text.split("\n")) {
    const line = raw.trim();
    if (!line.startsWith("data:")) continue;
    const data = line.slice(5).trim();
    if (!data || data === "[DONE]") continue;
    try {
      last = JSON.parse(data);
    } catch (e) {
      /* keep scanning: a later data line may hold the complete message */
    }
  }
  return last;
}

/* One JSON-RPC round trip over POST /mcp. Handles plain JSON and SSE bodies,
 * captures the Mcp-Session-Id header, and raises JSON-RPC errors as Errors. */
async function rpc(method, params) {
  const headers = {
    "Content-Type": "application/json",
    Accept: "application/json, text/event-stream",
  };
  if (session.sessionId) headers["Mcp-Session-Id"] = session.sessionId;
  if (session.protocolVersion) headers["MCP-Protocol-Version"] = session.protocolVersion;

  const isNotification = params === undefined;
  const body = isNotification
    ? { jsonrpc: "2.0", method }
    : { jsonrpc: "2.0", id: rpcId++, method, params };

  let resp;
  try {
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), REQUEST_TIMEOUT_MS);
    resp = await fetch(MCP_URL, {
      method: "POST",
      headers,
      body: JSON.stringify(body),
      signal: ctrl.signal,
    });
    clearTimeout(timer);
  } catch (e) {
    throw new Error("CONNECTION_FAILED");
  }

  const sid = resp.headers.get("mcp-session-id");
  if (sid) session.sessionId = sid;

  if (!resp.ok) throw new Error("HTTP_" + resp.status);

  const text = await resp.text();
  if (!text) return null; /* e.g. 202 Accepted for notifications */

  const contentType = resp.headers.get("content-type") || "";
  let msg = null;
  if (contentType.includes("text/event-stream")) {
    msg = parseSseMessage(text);
  } else {
    try {
      msg = JSON.parse(text);
    } catch (e) {
      throw new Error("BAD_RESPONSE");
    }
  }
  if (!msg) throw new Error("BAD_RESPONSE");
  if (msg.error) {
    const err = new Error(msg.error.message || "MCP error " + msg.error.code);
    err.code = msg.error.code;
    err.data = msg.error.data;
    throw err;
  }
  return msg.result === undefined ? msg : msg.result;
}

/* initialize -> notifications/initialized -> tools/list, with protocol fallback. */
async function ensureSession() {
  if (session.ready) return;
  let lastErr = null;
  for (const pv of PROTOCOL_VERSIONS) {
    try {
      const initResult = await rpc("initialize", {
        protocolVersion: pv,
        capabilities: {},
        clientInfo: CLIENT_INFO,
      });
      session.protocolVersion = (initResult && initResult.protocolVersion) || pv;
      await rpc("notifications/initialized");
      const listResult = await rpc("tools/list", {});
      session.tools = (listResult && listResult.tools) || [];
      session.ready = true;
      return;
    } catch (e) {
      lastErr = e;
      session.protocolVersion = null;
      session.sessionId = null;
    }
  }
  throw lastErr || new Error("INIT_FAILED");
}

async function callTool(name, args) {
  return rpc("tools/call", { name, arguments: args });
}

/* ---- Simulated routing ------------------------------------------------- */

function routeQuestion(question) {
  const q = question.toLowerCase();
  let best = null;
  for (const route of ROUTES) {
    const matched = route.keywords.filter((k) => q.includes(k));
    if (!best || matched.length > best.matched.length) {
      best = { tool: route.tool, matched, topic: route.topic };
    }
  }
  if (!best || best.matched.length === 0) {
    return {
      tool: "signal_scan",
      matched: [],
      reason: "the question did not match any tool keywords, so a broad scan is the safe default.",
    };
  }
  return {
    tool: best.tool,
    matched: best.matched,
    reason: "the question asks about " + best.topic + ".",
  };
}

/* Build tool arguments from the tool's own inputSchema (fetched via
 * tools/list). String fields whose names look like a question slot receive
 * the user's question; other required fields get neutral defaults. */
function buildArgs(tool, question) {
  const args = {};
  const schema = (tool && tool.inputSchema) || {};
  const props = schema.properties || {};
  const required = schema.required || [];
  const entries = Object.entries(props);

  let questionPlaced = false;
  for (const [name, def] of entries) {
    const t = def && def.type;
    if (t === "string") {
      if (/question|query|prompt|text|input|topic|event|symbol|market|utterance/i.test(name)) {
        args[name] = question;
        questionPlaced = true;
      } else if (required.includes(name)) {
        args[name] = "";
      }
    } else if (t === "number" || t === "integer") {
      if (required.includes(name)) args[name] = 0;
    } else if (t === "boolean") {
      if (required.includes(name)) args[name] = false;
    } else if (t === "array") {
      if (required.includes(name)) args[name] = [];
    } else if (t === "object") {
      if (required.includes(name)) args[name] = {};
    }
  }
  if (!questionPlaced) {
    const firstString = entries.find(([, def]) => def && def.type === "string");
    if (firstString) {
      args[firstString[0]] = question;
      questionPlaced = true;
    }
  }
  if (!questionPlaced) args.question = question;
  return args;
}

/* ---- Answer extraction and speech rules -------------------------------- */

/* Confidence is always rendered qualitatively: a number becomes a word. */
function qualitativeConfidence(c) {
  if (c === null || c === undefined || c === "") return "not stated";
  if (typeof c === "number") {
    if (!Number.isFinite(c) || c < 0 || c > 1) return "not stated";
    if (c >= 0.7) return "high";
    if (c >= 0.4) return "moderate";
    return "low";
  }
  return String(c);
}

/* Numbers in the detail payload are rounded for display so the UI never
 * implies false precision. The spoken strings are shown verbatim. */
function tidyNumbers(key, value) {
  if (typeof value === "number" && Number.isFinite(value) && !Number.isInteger(value)) {
    return Number(value.toFixed(4));
  }
  return value;
}

/* Turn a tools/call result into renderable parts. Prefers the tool's own
 * spoken string; renders honest silence when there is nothing to say. */
function extractAnswer(result) {
  if (!result || !Array.isArray(result.content) || result.content.length === 0) {
    return { silence: "The tool returned no content.", detail: result || null };
  }
  const texts = result.content
    .filter((c) => c && c.type === "text" && typeof c.text === "string")
    .map((c) => c.text)
    .join("\n")
    .trim();

  let payload = null;
  try {
    payload = JSON.parse(texts);
  } catch (e) {
    payload = null;
  }

  if (payload && typeof payload === "object") {
    return {
      spoken: payload.spoken || payload.summary || null,
      verdict: payload.verdict || null,
      confidence: qualitativeConfidence(payload.confidence),
      freshness: payload.data_freshness || payload.dataFreshness || null,
      detail: payload.detail !== undefined ? payload.detail : payload,
      isError: !!result.isError,
      errorText: result.isError ? texts : null,
    };
  }
  return {
    spoken: texts || null,
    verdict: null,
    confidence: "not stated",
    freshness: null,
    detail: texts,
    isError: !!result.isError,
  };
}

/* ---- Rendering (DOM) ---------------------------------------------------- */

function el(tag, cls, text) {
  const node = document.createElement(tag);
  if (cls) node.className = cls;
  if (text !== undefined && text !== null) node.textContent = text;
  return node;
}

function setRing(mode) {
  const ring = document.getElementById("ring");
  ring.className = "ring " + mode;
}

function setStateLine(text) {
  document.getElementById("stateLine").textContent = text;
}

function setConn(mode, text) {
  const pill = document.getElementById("connPill");
  pill.className = "conn " + mode;
  document.getElementById("connText").textContent = text;
}

function showBanner() {
  document.getElementById("serverBanner").classList.remove("hidden");
}
function hideBanner() {
  document.getElementById("serverBanner").classList.add("hidden");
}

function appendUser(question) {
  const wrap = el("div", "msg user");
  wrap.appendChild(el("div", "user-bubble", question));
  document.getElementById("transcript").appendChild(wrap);
  wrap.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function appendAlexaBlock() {
  const wrap = el("div", "msg");
  const block = el("div", "alexa-block");
  wrap.appendChild(block);
  document.getElementById("transcript").appendChild(wrap);
  return block;
}

async function playTrace(block, lines) {
  const trace = el("div", "trace");
  block.appendChild(trace);
  for (const line of lines) {
    const div = el("div", "trace-line" + (line.cls ? " " + line.cls : ""), line.text);
    trace.appendChild(div);
    trace.scrollIntoView({ behavior: "smooth", block: "nearest" });
    await sleep(line.pause !== undefined ? line.pause : 650);
  }
  return trace;
}

function metaItem(k, v) {
  const s = el("span", "meta-item");
  s.appendChild(el("span", "meta-k", k + ":"));
  s.appendChild(el("span", "meta-v", v));
  return s;
}

function renderAnswer(block, answer, route) {
  const card = el("div", "answer-card");

  if (answer.isError) {
    card.appendChild(el("div", "verdict error", "The tool reported an error."));
    card.appendChild(el("p", "spoken", answer.errorText || "No further detail was provided."));
  } else if (!answer.spoken && !answer.verdict) {
    card.appendChild(el("p", "spoken silence",
      answer.silence || "The tool returned data but no spoken summary. The detail payload is below."));
  } else {
    if (answer.verdict) card.appendChild(el("div", "verdict", answer.verdict));
    if (answer.spoken) {
      card.appendChild(el("p", "spoken", answer.spoken));
    } else {
      card.appendChild(el("p", "spoken silence",
        "The tool returned a verdict but no spoken summary. The detail payload is below."));
    }
  }

  const meta = el("div", "meta");
  meta.appendChild(metaItem("Confidence", answer.confidence || "not stated"));
  meta.appendChild(metaItem("Data freshness", answer.freshness || "not stated"));
  meta.appendChild(metaItem("Tool", route.tool + " (real call)"));
  card.appendChild(meta);

  card.appendChild(el("p", "offer", "Full detail payload is one question away: expand it below."));

  const details = el("details", "detail");
  const summary = el("summary", "", "Detail payload (numbers rounded for display)");
  const pre = el("pre", "", JSON.stringify(answer.detail, tidyNumbers, 2));
  details.appendChild(summary);
  details.appendChild(pre);
  card.appendChild(details);

  block.appendChild(card);
  card.scrollIntoView({ behavior: "smooth", block: "nearest" });
  requestAnimationFrame(() => card.classList.add("in"));
}

function renderConnError(block) {
  const card = el("div", "answer-card in");
  card.appendChild(el("div", "verdict error", "MCP server not reachable."));
  card.appendChild(el("p", "spoken",
    "I could not reach the MCP server at localhost:8000. Start the MCP server, then press Retry above and ask again."));
  block.appendChild(card);
}

function renderToolError(block, err) {
  const card = el("div", "answer-card in");
  card.appendChild(el("div", "verdict error", "Something went wrong calling the tool."));
  card.appendChild(el("p", "spoken", String((err && err.message) || err)));
  block.appendChild(card);
}

/* Glow the ring while the answer "speaks", scaled to the spoken length. */
function speakEffect(spoken) {
  const ms = spoken
    ? Math.min(8000, Math.max(2200, spoken.length * 18))
    : 2000;
  setRing("speaking");
  setStateLine("Speaking...");
  state.speakingUntil = Date.now() + ms;
  setTimeout(() => {
    if (!state.busy) {
      setRing("idle");
      setStateLine("Ask me about the markets.");
    }
  }, ms);
}

async function handleAsk(rawQuestion) {
  const question = (rawQuestion || "").trim();
  if (!question || state.busy) return;
  state.busy = true;
  setRing("thinking");
  setStateLine("Thinking...");

  appendUser(question);
  const block = appendAlexaBlock();

  try {
    await ensureSession();
    hideBanner();
    setConn("ok", "MCP server: connected (" + session.tools.length + " tools)");

    const route = routeQuestion(question);
    const traceLines = [
      { text: "Considering tools: " + TOOL_NAMES.join(", ") },
      route.matched.length > 0
        ? { text: 'Keyword scan matched: "' + route.matched.join('", "') + '"' }
        : { text: "Keyword scan matched no tool keywords; using the default." },
      { text: "Selected: " + route.tool + ", because " + route.reason },
      { text: "Simulated agent routing: keyword match", cls: "sim-label" },
      { text: "Calling " + route.tool + " on the MCP server...", pause: 400 },
    ];
    await playTrace(block, traceLines);

    const tool = (session.tools || []).find((t) => t.name === route.tool) || { name: route.tool };
    const args = buildArgs(tool, question);
    const result = await callTool(route.tool, args);
    const answer = extractAnswer(result);
    renderAnswer(block, answer, route);
    speakEffect(answer.spoken);
  } catch (e) {
    const msg = String((e && e.message) || e);
    if (msg === "CONNECTION_FAILED" || msg.indexOf("HTTP_") === 0) {
      setRing("error");
      setConn("bad", "MCP server: not reachable");
      showBanner();
      renderConnError(block);
    } else {
      setRing("error");
      renderToolError(block, e);
    }
  } finally {
    state.busy = false;
    if (Date.now() >= state.speakingUntil) {
      setRing("idle");
      setStateLine("Ask me about the markets.");
    }
  }
}

async function connectOnLoad() {
  setConn("checking", "MCP server: checking");
  try {
    await ensureSession();
    hideBanner();
    setConn("ok", "MCP server: connected (" + session.tools.length + " tools)");
  } catch (e) {
    setConn("bad", "MCP server: not reachable");
    showBanner();
  }
}

function init() {
  const form = document.getElementById("askForm");
  const input = document.getElementById("askInput");

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const q = input.value;
    input.value = "";
    input.focus();
    handleAsk(q);
  });

  document.querySelectorAll(".chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      input.value = chip.getAttribute("data-q");
      handleAsk(chip.getAttribute("data-q"));
    });
  });

  document.getElementById("retryBtn").addEventListener("click", () => {
    hideBanner();
    connectOnLoad();
  });

  connectOnLoad();

  /* Deep link for the demo video and headless checks: web/index.html?q=... */
  const preset = new URLSearchParams(window.location.search).get("q");
  if (preset) {
    input.value = preset;
    setTimeout(() => handleAsk(preset), 400);
  }
}

if (typeof document !== "undefined" && document.addEventListener) {
  document.addEventListener("DOMContentLoaded", init);
}

/* Exposed for headless testing; harmless in the browser. */
globalThis.AlphaVoice = {
  routeQuestion,
  buildArgs,
  qualitativeConfidence,
  tidyNumbers,
  extractAnswer,
  parseSseMessage,
  rpc,
  ensureSession,
  callTool,
  session,
  TOOL_NAMES,
  ROUTES,
};
