# BWC Report — clip_02_lapd_armed_suspect_restraining_order.mp4

- **Generated:** 2026-04-11T04:27:25.574542+00:00
- **Asset ID:** `69d9cd8d552f54b600147d18`
- **Model:** `pegasus1.2`
- **SHA-256:** `ab83fc4b35ddfe37c1e840915c5367bbb86c4b46f2f5b0436ff29d0cefd490a5`

## Triage
- **Priority:** **Urgent**
- **Reasoning:** The clip contains a prolonged verbal altercation between officers and a subject who refuses to comply with commands to move away from a doorway. Multiple officers issue repeated verbal commands to stand still and move away from the door, with escalating language including threats of force and claims that the subject will be shot. At 03:54:00, a weapon is drawn, confirming a high-risk situation. The subject repeatedly states he will not be taken to jail and insists he will be shot, indicating a clear escalation of tension. These events, combined with the drawn weapon and sustained verbal confrontation, meet the criteria for 'Urgent' priority due to the presence of a weapon and active verbal escalation with potential for use of force.
- **Prompt / schema version:** `v1` / `v1`

### Events
- `02:28:00` — **verbal_command** (confidence 0.95)
- `02:38:00` — **verbal_command** (confidence 0.95)
- `02:48:00` — **verbal_command** (confidence 0.90)
- `02:58:00` — **verbal_command** (confidence 0.90)
- `03:08:00` — **verbal_command** (confidence 0.90)
- `03:18:00` — **verbal_command** (confidence 0.90)
- `03:29:00` — **verbal_command** (confidence 0.85)
- `03:39:00` — **verbal_command** (confidence 0.80)
- `03:54:00` — **weapon_drawn** (confidence 0.95)
- `04:24:00` — **verbal_escalation** (confidence 0.90)
- `04:34:00` — **verbal_escalation** (confidence 0.90)
- `05:06:00` — **verbal_command** (confidence 0.90)
- `05:16:00` — **verbal_escalation** (confidence 0.90)
- `05:31:00` — **verbal_escalation** (confidence 0.85)
- `05:49:00` — **verbal_escalation** (confidence 0.90)
- `06:17:00` — **verbal_command** (confidence 0.85)
- `06:32:00` — **verbal_escalation** (confidence 0.90)
- `06:46:00` — **verbal_escalation** (confidence 0.90)
- `07:01:00` — **verbal_escalation** (confidence 0.80)

## Policy Compliance
- **Prompt / schema version:** `v1` / `v1`
- **Reasoning:** The officer repeatedly used calm, clear commands and emphasized the subject was not under arrest, demonstrating de-escalation efforts from 01:33 to 03:08. Despite these efforts, the subject refused to move from near the doorway, creating a safety concern. At 05:41, officers initiated physical restraint after the subject resisted, which escalated the encounter. The positioning shifted from safe distance to close contact during the struggle, reducing de-escalation effectiveness. Miranda rights were not read, and no arrest was formally announced during the clip, so delivery is not applicable.

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
      "timestamp": "01:33:00",
      "technique": "clear_command",
      "quote": "Hey, Pete. It's the police.",
      "confidence": 0.98
    },
    {
      "timestamp": "01:43:00",
      "technique": "calm_tone",
      "quote": "You're not under arrest, dude.",
      "confidence": 0.97
    },
    {
      "timestamp": "02:18:00",
      "technique": "distance_creation",
      "quote": "Come over here, away from the door.",
      "confidence": 0.96
    },
    {
      "timestamp": "02:38:00",
      "technique": "active_listening",
      "quote": "I'm giving you my word, dude.",
      "confidence": 0.95
    },
    {
      "timestamp": "03:08:00",
      "technique": "clear_command",
      "quote": "Look between these two doors.",
      "confidence": 0.94
    }
  ],
  "use_of_force": {
    "type": "physical_restraint",
    "timestamp": "05:41:00",
    "description": "Officers attempted to handcuff the subject, who resisted, leading to a physical struggle.",
    "confidence": 0.99
  },
  "positioning": {
    "assessment": "The officer maintained a consistent distance from the subject during initial interaction, avoiding close proximity. However, as resistance escalated, officers moved in closely and attempted to restrain the subject, which increased physical risk and reduced de-escalation potential.",
    "confidence": 0.97
  },
  "reasoning": "The officer repeatedly used calm, clear commands and emphasized the subject was not under arrest, demonstrating de-escalation efforts from 01:33 to 03:08. Despite these efforts, the subject refused to move from near the doorway, creating a safety concern. At 05:41, officers initiated physical restraint after the subject resisted, which escalated the encounter. The positioning shifted from safe distance to close contact during the struggle, reducing de-escalation effectiveness. Miranda rights were not read, and no arrest was formally announced during the clip, so delivery is not applicable."
}
```
