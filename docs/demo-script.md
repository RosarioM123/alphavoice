# AlphaVoice demo script (60 seconds)

Read this aloud while recording. Speak naturally, not rushed. Timing cues are approximate.

**0:00 to 0:20: the hook**

"AlphaVoice is a translation layer between quant models and human conversation. It is a self-hosted MCP server that turns an Alexa+ agent into a quant research desk. The centerpiece is the composed path: one spoken question, three quant engines, one spoken brief. Watch."

**0:20 to 0:45: the centerpiece, the composed morning brief**

Ask: "Alexa, morning brief roundup: this morning's CPI print, anything mispriced, and today's signals."

The agent selects the market_brief tool, which runs news_microstructure, mispricing_check, and signal_scan in-process on the synthetic fixtures and synthesizes one spoken verdict. The answer you hear is in this exact shape, the real output, spoken aloud:

"News is absorbed with a half-life of about 30 seconds; mispricing leaves a net edge of about 0.05 per contract, though the Kelly sizer recommends no position, paper only; and the signal scan ranks MSFT first, with about 1.6 percent expected return over 5 days. Say which lens to unpack: news absorption, mispricing, or the signal ranking."

**0:45 to 0:55: the honesty beat**

"Every number you heard is synthetic and labeled simulated. The mispricing leg is paper only, nothing executes, no order path exists. The point is the composition pattern: single-purpose MCP tools as building blocks, one composed voice on top."

**0:55 to 1:00: the close**

"AlphaVoice. Quant models you can talk to. Built for the Alexa+ track of the Amazon Developer Hackathon, and open sourced for the Open Source mini challenge."
