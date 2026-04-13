# BWC Report — clip_01_nypd_107pct_ois_20260126.mp4

- **Generated:** 2026-04-13T02:41:08.927729+00:00
- **Asset ID:** `69dc57a017f262cc78ba0948`
- **Model:** `pegasus1.2`
- **SHA-256:** `1deb829e2c29bd5a6135751b91765c77135b105e076da7c09cefc3b78754cfd8`

## Triage
- **Priority:** **Urgent**
- **Reasoning:** The clip shows a police officer drawing his firearm at 10:38:00 during a confrontation in a residential living area. Shots are fired at 10:42:00, immediately followed by a subject being observed on the ground at 10:44:00, indicating a use-of-force incident. The camera angle shifts abruptly after the shots, suggesting the officer may have been struck, supporting the inference of an officer-down event. These events meet the criteria for 'Urgent' priority due to lethal force use and potential officer injury.
- **Prompt / schema version:** `v1` / `v1`

### Events
- `10:38:00` — **weapon_drawn** (confidence 0.95)
- `10:42:00` — **shots_fired** (confidence 0.98)
- `10:44:00` — **subject_down** (confidence 0.92)
- `10:44:00` — **officer_down** (confidence 0.88)

## Policy Compliance
- **Prompt / schema version:** `v1` / `v1`
- **Reasoning:** No Miranda rights were delivered during the clip, as no arrest or custodial interrogation occurred. The suspect was shot at 12:20 after advancing with a knife. No de-escalation techniques were observed in the audio or visual record. The use of lethal force was initiated at 12:20 when the officer fired multiple rounds. Officer positioning remained consistent with de-escalation principles—maintaining distance and avoiding aggressive postures—despite the suspect's aggressive advance.

### Raw finding
```json
{
  "miranda": {
    "delivered": false,
    "timestamp": "",
    "quote": "",
    "confidence": 0.95
  },
  "deescalation": [],
  "use_of_force": {
    "type": "lethal_force",
    "timestamp": "12:20",
    "description": "Officer discharged multiple rounds from service weapon at suspect holding a knife, resulting in fatal injury.",
    "confidence": 0.98
  },
  "positioning": {
    "assessment": "Officers maintained a defensive distance from the suspect after he emerged with a knife, retreating slightly while keeping visual contact. No positioning suggesting corner-pinning or weapon display without threat was observed.",
    "confidence": 0.92
  },
  "reasoning": "No Miranda rights were delivered during the clip, as no arrest or custodial interrogation occurred. The suspect was shot at 12:20 after advancing with a knife. No de-escalation techniques were observed in the audio or visual record. The use of lethal force was initiated at 12:20 when the officer fired multiple rounds. Officer positioning remained consistent with de-escalation principles\u2014maintaining distance and avoiding aggressive postures\u2014despite the suspect's aggressive advance."
}
```
