"""Policy compliance auditor: Miranda, de-escalation, UoF, positioning.

Same API pattern as triage.py — Pegasus analyze with a structured JSON
response — but loads a different prompt/schema pair. Kept as a separate
file rather than a shared helper because the two may diverge (different
max_tokens, different post-processing) as we iterate.
"""

from __future__ import annotations

import json

from twelvelabs.types import ResponseFormat, VideoContext_AssetId

from .config import COMPLIANCE_VERSION, get_client, load_prompt, load_schema


def compliance(asset_id: str, max_tokens: int = 4096) -> dict:
    """Audit the clip and return parsed JSON matching schemas/compliance.<ver>.json.

    max_tokens is set to the documented Pegasus hard cap (4096) because the
    compliance schema is deep (5 top-level fields, nested objects + arrays).
    The prompt also caps array sizes and quote lengths to keep responses
    inside the budget.
    """
    client = get_client()
    prompt = load_prompt("compliance", COMPLIANCE_VERSION)
    schema = load_schema("compliance", COMPLIANCE_VERSION)

    result = client.analyze(
        video=VideoContext_AssetId(asset_id=asset_id),
        prompt=prompt,
        response_format=ResponseFormat(type="json_schema", json_schema=schema),
        max_tokens=max_tokens,
    )

    if getattr(result, "finish_reason", None) == "length":
        raise RuntimeError(
            "Compliance response truncated (finish_reason=length). "
            "Reduce schema complexity or raise max_tokens."
        )

    data = json.loads(result.data) if result.data else {}
    data["_prompt_version"] = COMPLIANCE_VERSION
    data["_schema_version"] = COMPLIANCE_VERSION
    return data
