"""Body-cam triage classifier: Urgent / Standard / Archive with evidence.

Calls Pegasus via client.analyze() with a JSON-schema response format.
The prompt and schema are loaded from versioned files on disk so every
report can cite the exact prompt + schema used to produce it.

See https://docs.twelvelabs.io/v1.3/docs/guides/analyze-videos/structured-responses
"""

from __future__ import annotations

import json

from twelvelabs.types import ResponseFormat, VideoContext_AssetId

from .config import TRIAGE_VERSION, get_client, load_prompt, load_schema


def triage(asset_id: str, max_tokens: int = 2048) -> dict:
    """Classify the clip and return parsed JSON matching schemas/triage.<ver>.json.

    The returned dict is annotated with _prompt_version and _schema_version
    so the downstream report can cite them for chain-of-custody purposes.
    """
    client = get_client()
    prompt = load_prompt("triage", TRIAGE_VERSION)
    schema = load_schema("triage", TRIAGE_VERSION)

    result = client.analyze(
        video=VideoContext_AssetId(asset_id=asset_id),
        prompt=prompt,
        response_format=ResponseFormat(type="json_schema", json_schema=schema),
        max_tokens=max_tokens,
    )

    if getattr(result, "finish_reason", None) == "length":
        raise RuntimeError(
            "Triage response truncated (finish_reason=length). "
            "Reduce schema complexity or raise max_tokens."
        )

    data = json.loads(result.data) if result.data else {}
    data["_prompt_version"] = TRIAGE_VERSION
    data["_schema_version"] = TRIAGE_VERSION
    return data
