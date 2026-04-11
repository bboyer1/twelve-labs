"""Project-wide configuration: client, paths, and version constants.

All runtime constants live here so the rest of the code reads them by name.
Prompts and schemas are versioned files on disk (in prompts/ and schemas/),
never inline Python constants — this is the explainability story.
"""

from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from twelvelabs import TwelveLabs

# --- Paths ------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
CLIPS_DIR = REPO_ROOT / "clips"
PROMPTS_DIR = REPO_ROOT / "prompts"
SCHEMAS_DIR = REPO_ROOT / "schemas"
OUTPUTS_DIR = REPO_ROOT / "outputs"
SAMPLES_DIR = REPO_ROOT / "samples"

# --- Versions ---------------------------------------------------------------

# Version suffix selects which prompt + schema files to load AND is recorded
# in every generated report for chain-of-custody / explainability.
TRIAGE_VERSION = "v1"
COMPLIANCE_VERSION = "v1"

# The analyze endpoint is backed by Pegasus; recorded in every report for
# audit trail. (The SDK doesn't require us to pass this — it's metadata.)
PEGASUS_MODEL = "pegasus1.2"

# --- Client -----------------------------------------------------------------

load_dotenv(REPO_ROOT / ".env")


@lru_cache(maxsize=1)
def get_client() -> TwelveLabs:
    """Singleton TwelveLabs client. Reads TWELVE_LABS_API_KEY from env.

    Note: SDK v1.2.2's TwelveLabs.__init__ does NOT auto-read the env var
    despite what the docs claim — we must pass api_key= explicitly.
    """
    api_key = os.getenv("TWELVE_LABS_API_KEY")
    if not api_key:
        raise RuntimeError(
            "TWELVE_LABS_API_KEY not set. Copy .env.example to .env and fill it in."
        )
    return TwelveLabs(api_key=api_key)


# --- Prompt + schema loading -----------------------------------------------


def load_prompt(name: str, version: str) -> str:
    """Load a prompt by name + version — e.g. load_prompt('triage', 'v1')."""
    path = PROMPTS_DIR / f"{name}.{version}.md"
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    return path.read_text()


def load_schema(name: str, version: str) -> dict:
    """Load a JSON schema by name + version — e.g. load_schema('triage', 'v1')."""
    path = SCHEMAS_DIR / f"{name}.{version}.json"
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {path}")
    return json.loads(path.read_text())
