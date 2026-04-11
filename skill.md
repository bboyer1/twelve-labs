# TwelveLabs API — Skill File

Dense, copy-paste-ready reference for the TwelveLabs v1.3 API and Python SDK. Built from the official docs. Read this before writing any code that touches TwelveLabs.

**Docs root:** https://docs.twelvelabs.io/v1.3/
**Full page map (for deeper lookups):** https://docs.twelvelabs.io/v1.3/llms.txt
**OpenAPI spec:** https://docs.twelvelabs.io/openapi.yaml

---

## 1. Models — Marengo vs Pegasus

TwelveLabs has two foundation models. **You cannot put them in the same index.** Pick the right model for the job; if you need both, create two indexes (or use Pegasus off raw assets without an index).

| | **Marengo** | **Pegasus** |
|---|---|---|
| Type | Embedding model | Generative (video MLLM) |
| What it does | Vector search over video (text, image, audio queries) + raw embeddings for RAG / vector DB | Summarize, classify, Q&A, open-ended text generation from video — with temporal grounding (timestamps) |
| Latest version | `marengo3.0` | `pegasus1.2` |
| Use when | You have many videos and users need to **find** things across them | You have one video and you need the system to **explain / classify / summarize** what's in it |
| Max video | 4 hours (continuous) | 2 hours, ≤ 2 GB |
| Structured JSON output | N/A (returns vectors / hits) | **Yes** — via `response_format=ResponseFormat(type="json_schema", ...)` |
| Right fit for | Cross-library search, RAG, recommendations | Triage, compliance checks, summarization, Q&A, anything where you want *text about the video* |

**Rule of thumb for the body-cam exercise:** triage, policy compliance, and summarization are all **Pegasus** jobs. Cross-library search is a **Marengo** job. FOIA redaction is mostly Pegasus (find PII segments) with Marengo as a secondary index if you need cross-library PII sweep.

**Deeper reading:**
- Marengo: https://docs.twelvelabs.io/v1.3/docs/concepts/models/marengo
- Pegasus: https://docs.twelvelabs.io/v1.3/docs/concepts/models/pegasus

---

## 2. Authentication

```
Header:    x-api-key: <YOUR_KEY>
Base URL:  https://api.twelvelabs.io/v1.3
```

Get a key at https://playground.twelvelabs.io/ → API Keys dashboard → "Create API Key".

The Python SDK reads `TWELVE_LABS_API_KEY` from the environment automatically, or you can pass `api_key=` to the constructor.

**Docs:** https://docs.twelvelabs.io/v1.3/api-reference/authentication

---

## 3. Python SDK — install + client

```bash
pip install twelvelabs python-dotenv
```

```python
import os
from dotenv import load_dotenv
from twelvelabs import TwelveLabs

load_dotenv()  # reads TWELVE_LABS_API_KEY from .env

# IMPORTANT: SDK v1.2.2 does NOT auto-read TWELVE_LABS_API_KEY from env
# despite what the docs claim. You MUST pass api_key= explicitly.
# inspect.signature(TwelveLabs.__init__) shows api_key as Optional with
# default None, but the actual runtime raises TypeError if you omit it.
client = TwelveLabs(api_key=os.environ["TWELVE_LABS_API_KEY"])
```

**Docs:** https://docs.twelvelabs.io/v1.3/sdk-reference/python/the-twelve-labs-class

---

## 4. Upload a video (direct upload, ≤ 200 MB)

Direct uploads are the simplest path. For files > 200 MB use the multipart upload API. Direct uploads are *synchronous* for small files — the call returns once the asset is created, then you poll until indexing is `"ready"`.

```python
import time

# Upload from a local file
asset = client.assets.create(
    method="direct",
    file=open("clips/bwc_clip_001.mp4", "rb"),
    filename="bwc_clip_001.mp4",
)

# Or upload from a URL
asset = client.assets.create(
    method="url",
    url="https://example.com/bwc_clip_001.mp4",
)

asset_id = asset.id
print(f"Uploaded. asset_id={asset_id}")

# Poll until ready
while True:
    asset = client.assets.retrieve(asset_id=asset_id)
    if asset.status == "ready":
        break
    if asset.status == "failed":
        raise RuntimeError(f"Asset processing failed: {asset_id}")
    print(f"  status={asset.status} — sleeping 5s")
    time.sleep(5)
```

**Status values:** `processing` → `ready` | `failed`.

**Docs:** https://docs.twelvelabs.io/v1.3/sdk-reference/python/upload-content/direct-uploads

---

## 5. Analyze a video (Pegasus) — the critical primitive

Once the asset is `ready`, you can call `client.analyze()` directly on the asset ID. **No index required for analyze.**

### 5a. Plain-text prompt (simplest case)

```python
from twelvelabs.types import VideoContext_AssetId

text = client.analyze(
    video=VideoContext_AssetId(asset_id=asset_id),
    prompt="Summarize this body-worn camera clip. Note any escalation, weapon visibility, or use-of-force events with timestamps.",
)
print(text.data)
```

There's also `client.analyze_stream(...)` which yields chunks as Pegasus generates. For scripts, plain `analyze()` is simpler; streaming is better for UIs.

### 5b. **Structured JSON output — THE pattern for triage & compliance**

This is the single most important endpoint for our use case. It takes a raw JSON-schema dict (not a Pydantic model) via `response_format`, and Pegasus returns JSON that matches the schema.

```python
import json
from twelvelabs import TwelveLabs
from twelvelabs.types import ResponseFormat, VideoContext_AssetId

triage_schema = {
    "type": "object",
    "properties": {
        "priority": {
            "type": "string",
            "pattern": "^(Urgent|Standard|Archive)$"  # enum workaround — see § 6
        },
        "events": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "timestamp": {"type": "string", "pattern": "^\\d{2}:\\d{2}:\\d{2}$"},
                    "type":      {"type": "string"},
                    "confidence":{"type": "number"}  # range enforced via prompt — see § 6
                },
                "required": ["timestamp", "type", "confidence"]
            }
        },
        "reasoning": {"type": "string"}
    },
    "required": ["priority", "events", "reasoning"]
}

text = client.analyze(
    video=VideoContext_AssetId(asset_id=asset_id),
    prompt=(
        "You are a body-worn camera triage classifier. "
        "Classify this clip as Urgent, Standard, or Archive. "
        "Urgent = use-of-force, weapon drawn, verbal altercation, officer-down. "
        "Return timestamped events and reasoning."
    ),
    response_format=ResponseFormat(type="json_schema", json_schema=triage_schema),
    max_tokens=2048,  # cap to avoid truncation on long clips
)

data = json.loads(text.data) if text.data else {}
if getattr(text, "finish_reason", None) == "length":
    print("WARNING: response truncated — tighten schema or raise max_tokens")
print(json.dumps(data, indent=2))
```

**Docs:** https://docs.twelvelabs.io/v1.3/docs/guides/analyze-videos/structured-responses

---

## 6. JSON-schema keyword support (important gotcha)

The v1.3 analyze endpoint supports a **restricted subset** of JSON Schema. Unsupported keywords cause a `response_format_invalid` error.

| Keyword | Supported? | Notes |
|---|---|---|
| `type` | ✅ | |
| `properties`, `required` | ✅ | |
| `pattern` (string regex) | ✅ | Use this for enum-like constraints — confirmed working in v1.2.2 |
| `minimum`, `maximum` (number/int) | ❌ | **Confirmed broken in v1.2.2** despite the docs claiming support. Server returns `response_format_invalid: numeric constraints ('minimum') are not supported`. Strip them from schemas and validate client-side or enforce via prompt. |
| `minItems` (array) | ⚠️ | Docs claim 0/1 only — not personally verified, treat as untrusted |
| `enum` | ❌ | **Use `pattern: "^(A|B|C)$"` instead** |
| `minLength`, `maxLength` | ❌ | Enforce in prompt + client-side validation |
| `maxItems` | ❌ (not confirmed supported) | Cap via prompt + validate |

**Workaround for enums** — pick one:
1. `{"type": "string", "pattern": "^(Urgent|Standard|Archive)$"}` (server-validated)
2. Tell the model in the prompt and re-validate in Python after parsing

Also cap `max_tokens` (hard ceiling: 4096) and always check `finish_reason == "length"` to detect truncation.

---

## 7. Search (Marengo)

Only relevant if we add Cross-Library Search. Search needs an explicit index with Marengo enabled.

```python
from twelvelabs.indexes import IndexesCreateRequestModelsItem

# 1. Create a Marengo index
index = client.indexes.create(
    index_name="bwc_search_2026",
    models=[
        IndexesCreateRequestModelsItem(
            model_name="marengo3.0",
            model_options=["visual", "audio"],
        )
    ],
)

# 2. Upload videos into the index (direct or multipart as above)
# 3. Run a natural-language search
results = client.search.query(
    index_id=index.id,
    query_text="officer drew a firearm during a vehicle stop",
    search_options=["visual", "audio"],
)
for hit in results.data:
    print(hit.video_id, hit.start, hit.end, hit.score, hit.confidence)
```

**Docs:**
- https://docs.twelvelabs.io/v1.3/sdk-reference/python/manage-indexes
- https://docs.twelvelabs.io/v1.3/sdk-reference/python/search
- https://docs.twelvelabs.io/v1.3/docs/guides/search

---

## 8. Rate limits & errors

- Rate limits vary by plan. If you hit `429`, back off exponentially. The exercise brief says you can contact the recruiter for a temporary bump.
- Common errors: `response_format_invalid` (bad schema keyword), `asset_not_ready` (polling race), `rate_limit_exceeded`, `authentication_failed`.
- Async analyze tasks exist (`create_async_analysis_task`) for long videos where you don't want to block — pair with webhooks for completion notifications.

**Docs:**
- https://docs.twelvelabs.io/v1.3/docs/get-started/rate-limits
- https://docs.twelvelabs.io/v1.3/api-reference/error-codes

---

## 9. Deployment surfaces worth knowing (for PS pitch)

- **Managed SaaS** — api.twelvelabs.io (what the SDK hits by default)
- **Amazon Bedrock** — Marengo and Pegasus are available as Bedrock foundation models. **This is the data-sovereignty story for government customers:** video never leaves the agency's AWS tenant, no data egress to TwelveLabs. Supports GovCloud paths.
- **Playground** — https://playground.twelvelabs.io/ — web UI for manual testing, good for showing non-technical stakeholders what Pegasus/Marengo can do without writing code.

**Docs:**
- Bedrock: https://docs.twelvelabs.io/v1.3/docs/cloud-partner-integrations/amazon-bedrock
- Playground: https://docs.twelvelabs.io/v1.3/docs/resources/playground

---

## 10. Quick reference — the 5 calls we actually use

```python
# 1. Client
client = TwelveLabs()

# 2. Upload
asset = client.assets.create(method="direct", file=open(path, "rb"), filename=name)

# 3. Poll
asset = client.assets.retrieve(asset_id=asset.id)  # check .status

# 4. Analyze (free-text)
out = client.analyze(video=VideoContext_AssetId(asset_id=aid), prompt="...")

# 5. Analyze (structured JSON) — the big one
out = client.analyze(
    video=VideoContext_AssetId(asset_id=aid),
    prompt="...",
    response_format=ResponseFormat(type="json_schema", json_schema=schema_dict),
    max_tokens=2048,
)
data = json.loads(out.data)
```

That's 95% of what the body-cam exercise needs.
