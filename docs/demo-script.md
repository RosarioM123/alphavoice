# AlphaVoice demo script (60 seconds)

Read this aloud while recording. Speak naturally, not rushed. Timing cues are approximate.

**0:00 to 0:15: the hook**

"AlphaVoice is a translation layer between quant models and human conversation. It is a self-hosted MCP server that turns an Alexa+ agent into a quant research desk. Watch: I ask a market question out loud, and the agent picks the right quant tool and answers it."

**0:15 to 0:40: beat one, the CPI print**

Ask: "Alexa, how fast did the market absorb this morning's CPI print?"

The agent selects the news_microstructure tool. The spoken answer you hear should be in this shape, half-life first, then plain-English impact, then verdict, then the offer:

"This morning's CPI print was absorbed with a half-life of about eleven minutes. In plain English: half the price impact landed within eleven minutes of the release. The Hawkes fit shows the regime is sub-critical, so the news did not cascade. Confidence is moderate, data is one hour fresh. Want the full impact curve?"

**0:40 to 0:55: optional beat two, mispricing (record this beat, keep it only if time allows)**

Ask: "Alexa, any mispricing on the election markets right now?"

The agent selects mispricing_check. The spoken answer should be in this shape:

"Full-book VWAP shows Kalshi pricing the contract two cents rich to Polymarket. Fractional Kelly suggests a small paper position. This is paper only, nothing executes. Want the exact size?"

**0:55 to 1:00: the close**

"AlphaVoice. Quant models you can talk to. Built for the Alexa+ track of the Amazon Developer Hackathon, and open sourced for the Open Source mini challenge."
