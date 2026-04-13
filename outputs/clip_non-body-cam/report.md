# BWC Report — clip_non-body-cam.mp4

- **Generated:** 2026-04-13T02:42:57.784793+00:00
- **Asset ID:** `69dc582717f262cc78ba0972`
- **Model:** `pegasus1.2`
- **SHA-256:** `95c501bb2c5555b6e20464c5ad434791cde7633d24356feec3b698fd523e9422`

## Triage
- **Priority:** **Archive**
- **Reasoning:** The video clip shows a person washing their hands at a bathroom sink with no visible interaction with others, no signs of distress, and no indication of police activity. There are no observable events that meet the criteria for 'Urgent' or 'Standard' classification. The audio contains only the word 'キャンディング' (likely a misheard or garbled utterance), which does not indicate any actionable event. Therefore, the clip is classified as 'Archive' due to the absence of any substantive or notable activity.
- **Prompt / schema version:** `v1` / `v1`

### Events
- `00:00:00` — **no_notable_event** (confidence 1.00)

## Policy Compliance
- **Prompt / schema version:** `v1` / `v1`
- **Reasoning:** The clip depicts a person washing their hands in a restroom, with no visible law enforcement personnel, subjects, or any interaction between individuals. There is no indication of an arrest, custodial interrogation, or use of force. The audio contains only the word 'キャンディング' (likely a misheard or garbled utterance), which does not constitute a Miranda rights delivery. No de-escalation techniques are observed, as there is no verbal exchange between officers and subjects. Officer-subject positioning is not applicable due to the absence of any personnel. The entire clip is non-interactive and non-incident-based, rendering all policy audit criteria inapplicable.

### Raw finding
```json
{
  "miranda": {
    "delivered": false,
    "timestamp": ":00:00",
    "quote": "",
    "confidence": 1
  },
  "deescalation": [],
  "use_of_force": {
    "type": "none",
    "timestamp": ":00:00",
    "description": "",
    "confidence": 1
  },
  "positioning": {
    "assessment": "The video shows a person washing their hands in a restroom setting with no visible officer or subject interaction. No positioning dynamics between officers and subjects are present.",
    "confidence": 1
  },
  "reasoning": "The clip depicts a person washing their hands in a restroom, with no visible law enforcement personnel, subjects, or any interaction between individuals. There is no indication of an arrest, custodial interrogation, or use of force. The audio contains only the word '\u30ad\u30e3\u30f3\u30c7\u30a3\u30f3\u30b0' (likely a misheard or garbled utterance), which does not constitute a Miranda rights delivery. No de-escalation techniques are observed, as there is no verbal exchange between officers and subjects. Officer-subject positioning is not applicable due to the absence of any personnel. The entire clip is non-interactive and non-incident-based, rendering all policy audit criteria inapplicable."
}
```
