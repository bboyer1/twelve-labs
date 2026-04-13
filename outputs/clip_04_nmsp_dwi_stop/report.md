# BWC Report — clip_04_nmsp_dwi_stop.mp4

- **Generated:** 2026-04-13T04:11:42.169532+00:00
- **Asset ID:** `69dc6cee95fdab3eada4576b`
- **Model:** `pegasus1.2`
- **SHA-256:** `6e7990c090d7c0b2811d1b5811213e80ce6bab50ce9628ad0ec4ed107084c08b`

## Triage
- **Priority:** **Standard**
- **Reasoning:** The clip captures a routine traffic stop that escalates to an arrest without any use of force. The officer observes the driver weaving through traffic and initiates a stop, then conducts a field sobriety test. The subject shows signs of impairment and difficulty complying with commands, but no physical restraint or escalation occurs. The arrest is carried out calmly, and the officer later discovers a child in the trunk, which prompts an emotional reaction. Despite the gravity of the discovery, the interaction remains non-confrontational, warranting a 'Standard' classification.
- **Prompt / schema version:** `v1` / `v1`

### Events
- `00:00:00` — **traffic_stop** (confidence 0.90)
- `00:00:20` — **verbal_command** (confidence 0.80)
- `00:00:40` — **subject_compliance** (confidence 0.70)
- `00:01:00` — **arrest_without_force** (confidence 0.90)

## Policy Compliance
- **Prompt / schema version:** `v1` / `v1`
- **Reasoning:** The officer's interaction with the woman was conducted with clear verbal commands and acknowledgment of her condition, observed at 01:18 and 01:23. No use of force was observed throughout the encounter. The officer maintained a safe distance and used his vehicle as cover, consistent with de-escalation protocols. Miranda rights were not delivered, as no arrest was formally announced during the clip. The overall conduct aligns with de-escalation standards, though the absence of Miranda delivery during a custodial arrest warrants review.

### Raw finding
```json
{
  "miranda": {
    "delivered": false,
    "timestamp": ":00:00",
    "quote": ":00:00",
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
      "quote": "Okay, just walk normal.",
      "confidence": 0.8
    }
  ],
  "use_of_force": {
    "type": "none",
    "timestamp": ":00:00",
    "description": ":00:00",
    "confidence": 1
  },
  "positioning": {
    "assessment": "The officer maintained a safe distance and used his vehicle as cover, which is consistent with de-escalation principles.",
    "confidence": 0.9
  },
  "reasoning": "The officer's interaction with the woman was conducted with clear verbal commands and acknowledgment of her condition, observed at 01:18 and 01:23. No use of force was observed throughout the encounter. The officer maintained a safe distance and used his vehicle as cover, consistent with de-escalation protocols. Miranda rights were not delivered, as no arrest was formally announced during the clip. The overall conduct aligns with de-escalation standards, though the absence of Miranda delivery during a custodial arrest warrants review."
}
```
