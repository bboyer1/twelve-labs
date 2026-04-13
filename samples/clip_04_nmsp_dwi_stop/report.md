# BWC Report — clip_04_nmsp_dwi_stop.mp4

- **Generated:** 2026-04-11T05:12:41.793042+00:00
- **Asset ID:** `69d9d834ae92f1290e600bea`
- **Model:** `pegasus1.2`
- **SHA-256:** `6e7990c090d7c0b2811d1b5811213e80ce6bab50ce9628ad0ec4ed107084c08b`

## Triage
- **Priority:** **Standard**
- **Reasoning:** The clip shows a routine traffic stop that escalates to an arrest without use of force. The officer observes the driver weaving through traffic and pulls her over. He issues verbal commands, and the driver shows difficulty complying, including trouble standing and speaking coherently. The officer arrests her at 01:02 after she fails field sobriety tests. Later, the officer discovers a child in the trunk, prompting a visible emotional reaction, which constitutes a welfare intervention. No use of force, weapons, or medical emergency requiring immediate aid is observed, so the priority remains 'Standard'.
- **Prompt / schema version:** `v1` / `v1`

### Events
- `00:00:00` — **traffic_stop** (confidence 0.90)
- `00:00:20` — **verbal_command** (confidence 0.80)
- `00:00:50` — **subject_compliance** (confidence 0.70)
- `00:01:02` — **subject_arrest** (confidence 0.90)
- `00:01:42` — **medical_aid** (confidence 0.80)

## Policy Compliance
- **Prompt / schema version:** `v1` / `v1`
- **Reasoning:** The officer did not read Miranda rights prior to arrest at 01:42, as no such audio was recorded. De-escalation techniques were used, including active listening at 01:18, clear commands at 01:23, and an aid offer at 01:31. No use of force occurred at any point, with the most severe action being verbal commands. Officer positioning remained consistent with de-escalation principles—maintaining distance and avoiding aggressive postures. All observations are grounded in direct visual and audio evidence from the clip.

### Raw finding
```json
{
  "miranda": {
    "delivered": false,
    "timestamp": ":01:42",
    "quote": "None heard",
    "confidence": 0.9
  },
  "deescalation": [
    {
      "timestamp": "01:18:00",
      "technique": "active_listening",
      "quote": "I understand.",
      "confidence": 0.8
    },
    {
      "timestamp": "01:23:00",
      "technique": "clear_command",
      "quote": "Stand on my light, stand on my light.",
      "confidence": 0.9
    },
    {
      "timestamp": "01:31:00",
      "technique": "aid_offer",
      "quote": "Okay, let's just walk normal.",
      "confidence": 0.8
    }
  ],
  "use_of_force": {
    "type": "none",
    "timestamp": ":01:42",
    "description": "No physical or verbal force beyond standard commands observed.",
    "confidence": 1
  },
  "positioning": {
    "assessment": "The officer maintained a consistent distance from the subject, avoided cornering, and did not display weapons. Positioning remained non-threatening throughout.",
    "confidence": 0.9
  },
  "reasoning": "The officer did not read Miranda rights prior to arrest at 01:42, as no such audio was recorded. De-escalation techniques were used, including active listening at 01:18, clear commands at 01:23, and an aid offer at 01:31. No use of force occurred at any point, with the most severe action being verbal commands. Officer positioning remained consistent with de-escalation principles\u2014maintaining distance and avoiding aggressive postures. All observations are grounded in direct visual and audio evidence from the clip."
}
```
