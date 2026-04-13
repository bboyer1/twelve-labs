# BWC Report — clip_01_nypd_107pct_ois_20260126.mp4

- **Generated:** 2026-04-11T04:32:52.896573+00:00
- **Asset ID:** `69d9ced2c6f6c60e0c83e0e1`
- **Model:** `pegasus1.2`
- **SHA-256:** `1deb829e2c29bd5a6135751b91765c77135b105e076da7c09cefc3b78754cfd8`

## Triage
- **Priority:** **Urgent**
- **Reasoning:** The clip begins with a police officer entering a residence, followed by a verbal altercation and immediate physical restraint of a subject. At 10:07:00, a blurred figure is seen struggling on a couch, indicating a high-risk situation. A weapon is clearly visible at 11:10:00, confirmed by the object's shape and context. Officers are seen drawing and aiming firearms at 10:21:00 and 10:14:00, respectively, indicating a use-of-force scenario. The presence of a knife, ongoing struggle, and armed officers collectively meet the criteria for 'Urgent' priority.
- **Prompt / schema version:** `v1` / `v1`

### Events
- `09:45:00` — **door_entry** (confidence 0.95)
- `09:46:00` — **verbal_altercation** (confidence 0.85)
- `10:01:00` — **physical_restraint** (confidence 0.90)
- `10:07:00` — **weapon_drawn** (confidence 0.80)
- `10:14:00` — **officer_entry** (confidence 0.95)
- `10:21:00` — **gun_aimed** (confidence 0.90)
- `10:38:00` — **struggle** (confidence 0.85)
- `11:10:00` — **knife_visible** (confidence 0.80)
- `11:16:00` — **continued_struggle** (confidence 0.80)

## Policy Compliance
- **Prompt / schema version:** `v1` / `v1`
- **Reasoning:** At 08:11:00, Officer White issued a clear command to 'Put the knife down' while maintaining distance, demonstrating active de-escalation. The officer continued to use calm language and maintained spatial control by closing the door behind him, preventing the subject from retreating. Despite repeated verbal commands, the subject advanced with the knife at 09:18:00, prompting the officer to discharge four rounds. The positioning remained non-threatening throughout, with no physical contact or weapon display prior to the shooting. No Miranda rights were read, as no custodial interrogation occurred in this clip. The use of lethal force was initiated only after the subject re-engaged with the weapon following multiple de-escalation attempts.

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
      "timestamp": "08:11:00",
      "technique": "clear_command",
      "quote": "Put the knife down.",
      "confidence": 0.98
    },
    {
      "timestamp": "08:11:00",
      "technique": "distance_creation",
      "quote": "",
      "confidence": 0.97
    },
    {
      "timestamp": "08:41:00",
      "technique": "calm_tone",
      "quote": "I'm not going to hurt you.",
      "confidence": 0.96
    },
    {
      "timestamp": "08:41:00",
      "technique": "active_listening",
      "quote": "I hear you.",
      "confidence": 0.94
    },
    {
      "timestamp": "09:18:00",
      "technique": "clear_command",
      "quote": "Stop moving. Drop the knife.",
      "confidence": 0.95
    }
  ],
  "use_of_force": {
    "type": "lethal_force",
    "timestamp": "09:18:00",
    "description": "Officer discharged four rounds at the subject after he advanced with a knife despite repeated verbal commands to drop it.",
    "confidence": 0.99
  },
  "positioning": {
    "assessment": "The officer maintained a consistent distance from the subject, positioned between him and the door, and closed it behind him to limit escape routes. This positioning was consistent with de-escalation by controlling access while avoiding physical proximity.",
    "confidence": 0.98
  },
  "reasoning": "At 08:11:00, Officer White issued a clear command to 'Put the knife down' while maintaining distance, demonstrating active de-escalation. The officer continued to use calm language and maintained spatial control by closing the door behind him, preventing the subject from retreating. Despite repeated verbal commands, the subject advanced with the knife at 09:18:00, prompting the officer to discharge four rounds. The positioning remained non-threatening throughout, with no physical contact or weapon display prior to the shooting. No Miranda rights were read, as no custodial interrogation occurred in this clip. The use of lethal force was initiated only after the subject re-engaged with the weapon following multiple de-escalation attempts."
}
```
