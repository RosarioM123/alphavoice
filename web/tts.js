"use strict";
/* AlphaVoice text-to-speech: free window.speechSynthesis, no backend, no keys, no network.
   Loaded after app.js (defer), so the DOM is ready. Attaches a "Read aloud" button to
   every .answer-card via MutationObserver and wires an autoplay toggle by id. */

(function () {
  var synth = window.speechSynthesis;
  var autoplayBtn = document.getElementById("autoplayBtn");

  /* Guard: if speechSynthesis is unavailable, hide the controls and do nothing. */
  if (!synth) {
    if (autoplayBtn) autoplayBtn.style.display = "none";
    return;
  }

  /* Pick a default English voice when one is available, else fall back to default. */
  var voice = null;
  function pickVoice() {
    var voices = synth.getVoices() || [];
    var i, v, en = null;
    for (i = 0; i < voices.length; i++) {
      v = voices[i];
      if (v.lang && v.lang.toLowerCase().indexOf("en") === 0) { en = v; break; }
    }
    voice = en || voices[0] || null;
  }
  pickVoice();
  /* Voices may load asynchronously (notably Chrome), so re-pick when they arrive. */
  if (typeof synth.addEventListener === "function") {
    synth.addEventListener("voiceschanged", pickVoice);
  }

  var speakingBtn = null;

  function stopSpeech() {
    /* cancel() clears pending and in-progress speech; harmless if nothing is queued. */
    if (synth.speaking || synth.pending) synth.cancel();
    if (speakingBtn) {
      speakingBtn.classList.remove("speaking");
      speakingBtn = null;
    }
  }

  function cardText(card) {
    var parts = [];
    var verdictEl = card.querySelector(".verdict");
    var spokenEl = card.querySelector(".spoken");
    var t;
    if (verdictEl) {
      t = (verdictEl.textContent || "").trim();
      if (t) parts.push(t);
    }
    if (spokenEl) {
      t = (spokenEl.textContent || "").trim();
      if (t) parts.push(t);
    }
    /* Error and silence cards carry their text in .verdict / .spoken already. */
    return parts.join(" ");
  }

  function speakCard(card, btn) {
    /* Second press on the same button cancels; any new speech cancels old speech. */
    if (speakingBtn === btn && (synth.speaking || synth.pending)) {
      stopSpeech();
      return;
    }
    var text = cardText(card);
    stopSpeech();
    if (!text) return;
    var utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1;
    utterance.pitch = 1;
    if (voice) utterance.voice = voice;
    utterance.onend = utterance.onerror = function () {
      if (speakingBtn === btn) {
        btn.classList.remove("speaking");
        speakingBtn = null;
      }
    };
    speakingBtn = btn;
    btn.classList.add("speaking");
    synth.speak(utterance);
  }

  function makeSpeakButton(card) {
    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "speak-btn";
    btn.setAttribute("aria-label", "Read aloud");
    btn.title = "Read aloud";
    btn.innerHTML =
      '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" ' +
      'stroke="currentColor" stroke-width="2" stroke-linecap="round" ' +
      'stroke-linejoin="round" aria-hidden="true">' +
      '<polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>' +
      '<path d="M15.5 8.5a5 5 0 0 1 0 7"></path>' +
      '<path d="M18.6 5.4a9 9 0 0 1 0 13.2"></path></svg>';
    btn.addEventListener("click", function () { speakCard(card, btn); });
    return btn;
  }

  var autoplay = false;
  if (autoplayBtn) {
    autoplayBtn.addEventListener("click", function () {
      autoplay = !autoplay;
      autoplayBtn.setAttribute("aria-pressed", String(autoplay));
      autoplayBtn.textContent = "Auto-speak: " + (autoplay ? "on" : "off");
      if (!autoplay) stopSpeech();
    });
  }

  function enhanceCard(card) {
    if (card.dataset.ttsReady) return;
    card.dataset.ttsReady = "1";
    var btn = makeSpeakButton(card);
    var row = document.createElement("div");
    row.className = "speak-row";
    row.appendChild(btn);
    var meta = card.querySelector(".meta");
    if (meta && meta.parentNode === card) {
      meta.after(row);
    } else {
      card.appendChild(row);
    }
    if (autoplay) speakCard(card, btn);
  }

  /* Cancel in-progress speech when the user submits a new question.
     addEventListener does not conflict with app.js's own listener. */
  var askForm = document.getElementById("askForm");
  if (askForm) {
    askForm.addEventListener("submit", function () { stopSpeech(); });
  }

  var transcript = document.getElementById("transcript");
  if (!transcript) return;
  var observer = new MutationObserver(function (mutations) {
    for (var i = 0; i < mutations.length; i++) {
      var added = mutations[i].addedNodes;
      for (var j = 0; j < added.length; j++) {
        var node = added[j];
        if (!node || node.nodeType !== 1) continue;
        var cards;
        if (node.classList && node.classList.contains("answer-card")) {
          cards = [node];
        } else if (typeof node.querySelectorAll === "function") {
          cards = Array.prototype.slice.call(node.querySelectorAll(".answer-card"));
        } else {
          cards = [];
        }
        for (var k = 0; k < cards.length; k++) enhanceCard(cards[k]);
      }
    }
  });
  observer.observe(transcript, { childList: true, subtree: true });
})();
