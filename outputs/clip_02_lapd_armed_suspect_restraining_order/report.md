# BWC Report — clip_02_lapd_armed_suspect_restraining_order.mp4

- **Generated:** 2026-04-13T02:41:54.315616+00:00
- **Asset ID:** `69dc57cbdd4af71977354ad6`
- **Model:** `pegasus1.2`
- **SHA-256:** `ab83fc4b35ddfe37c1e840915c5367bbb86c4b46f2f5b0436ff29d0cefd490a5`

## Triage
- **Priority:** **Urgent**
- **Reasoning:** The clip contains multiple high-risk events that meet the 'Urgent' threshold. At 03:54:00, an officer draws a firearm, escalating the situation. This is followed by shots fired at 04:33:00, confirmed by both audio and visual evidence. The subject is observed falling to the ground at 04:55:00, indicating injury from force. A handgun is clearly visible in the room at 05:42:00, and officers retreat while maintaining weapon focus at 05:55:00. Medical aid is administered at 06:20:00, confirming a critical incident requiring immediate response. These events collectively constitute a use-of-force scenario with lethal force and injury, warranting urgent classification.
- **Prompt / schema version:** `v1` / `v1`

### Events
- `03:54:00` — **weapon_drawn** (confidence 0.95)
- `04:33:00` — **shots_fired** (confidence 0.98)
- `04:55:00` — **subject_down** (confidence 0.92)
- `05:42:00` — **weapon_visible** (confidence 0.97)
- `05:55:00` — **officer_retreat** (confidence 0.94)
- `06:20:00` — **medical_aid** (confidence 0.96)

## Policy Compliance
- **Prompt / schema version:** `v1` / `v1`
- **Reasoning:** No Miranda rights were delivered during the encounter, as the subject was not formally arrested or subjected to custodial interrogation. The officer repeatedly emphasized the subject was not under arrest and was attempting to engage in conversation, which indicates a non-custodial context. The officer used multiple de-escalation techniques, including calm tone, clear commands, and offers of reassurance, particularly between 01:02:00 and 01:03:00. The positioning remained non-confrontational, with the officer maintaining distance and avoiding physical proximity or weapon display. No use of force was observed, either verbal or physical, and the encounter remained verbal throughout. The final exchange at 06:46–07:01, where the subject says 'I don't know if I got shot on that,' reflects emotional distress but not an actual use of force event.

### Raw finding
```json
{
  "miranda": {
    "delivered": false,
    "timestamp": "",
    "quote": "",
    "confidence": 0.95
  },
  "deescalation": [
    {
      "timestamp": "01:02:00",
      "technique": "calm_tone",
      "quote": "Hey, Pete. It's the police.",
      "confidence": 0.9
    },
    {
      "timestamp": "01:02:00",
      "technique": "clear_command",
      "quote": "What's wrong, man? Let me talk to you real quick, Pete.",
      "confidence": 0.85
    },
    {
      "timestamp": "01:02:00",
      "technique": "active_listening",
      "quote": "You're not under arrest, dude. Listen.",
      "confidence": 0.9
    },
    {
      "timestamp": "01:02:00",
      "technique": "distance_creation",
      "quote": "Stand over here so I can talk to you.",
      "confidence": 0.9
    },
    {
      "timestamp": "01:02:00",
      "technique": "aid_offer",
      "quote": "I'm giving you my word, dude.",
      "confidence": 0.88
    }
  ],
  "use_of_force": {
    "type": "none",
    "timestamp": "",
    "description": "",
    "confidence": 0.98
  },
  "positioning": {
    "assessment": "The officer maintained a consistent distance from the subject, positioning himself to avoid cornering or blocking escape routes. He repeatedly directed the subject to move away from the doorway, which suggests an effort to manage space and reduce perceived threat, consistent with de-escalation principles.",
    "confidence": 0.95
  },
  "reasoning": "No Miranda rights were delivered during the encounter, as the subject was not formally arrested or subjected to custodial interrogation. The officer repeatedly emphasized the subject was not under arrest and was attempting to engage in conversation, which indicates a non-custodial context. The officer used multiple de-escalation techniques, including calm tone, clear commands, and offers of reassurance, particularly between 01:02:00 and 01:03:00. The positioning remained non-confrontational, with the officer maintaining distance and avoiding physical proximity or weapon display. No use of force was observed, either verbal or physical, and the encounter remained verbal throughout. The final exchange at 06:46\u201307:01, where the subject says 'I don't know if I got shot on that,' reflects emotional distress but not an actual use of force event."
}
```
