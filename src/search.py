"""Cross-library Marengo search across indexed BWC footage.

Enables natural-language queries like "show me all footage where an
officer drew a firearm during a vehicle stop" across the full video
library — capability #4 from the exercise brief.

Requires a Marengo index with videos already indexed. Use setup_index()
to create the index and index existing assets, then query() to search.
"""

from __future__ import annotations

from dataclasses import dataclass

from twelvelabs.indexes import IndexesCreateRequestModelsItem

from .config import MARENGO_MODEL, get_client


@dataclass
class SearchHit:
    clip_name: str
    start: float
    end: float
    rank: int
    transcript: str

    @property
    def timestamp(self) -> str:
        """Format start-end as MM:SS-MM:SS."""
        def fmt(s: float) -> str:
            m, sec = divmod(int(s), 60)
            return f"{m:02d}:{sec:02d}"
        return f"{fmt(self.start)}-{fmt(self.end)}"


def setup_index(
    index_name: str = "bwc-marengo",
    asset_ids: dict[str, str] | None = None,
) -> str:
    """Create a Marengo index and index assets into it. Returns the index_id.

    asset_ids: mapping of clip_name → asset_id. If provided, each asset
    is indexed into the new index.
    """
    client = get_client()

    index = client.indexes.create(
        index_name=index_name,
        models=[IndexesCreateRequestModelsItem(
            model_name=MARENGO_MODEL,
            model_options=["visual", "audio"],
        )],
    )
    index_id = index.id

    if asset_ids:
        for name, aid in asset_ids.items():
            client.indexes.indexed_assets.create(index_id=index_id, asset_id=aid)

    return index_id


def query(
    index_id: str,
    query_text: str,
    max_results: int = 5,
) -> list[SearchHit]:
    """Run a natural-language search across the Marengo index."""
    import json as _json

    from .config import OUTPUTS_DIR

    client = get_client()

    # Build reverse lookup: indexed_asset_id → clip name
    # Step 1: asset_id → clip name (from indexes.json)
    aid_to_name: dict[str, str] = {}
    idx_file = OUTPUTS_DIR / "indexes.json"
    if idx_file.exists():
        assets = _json.loads(idx_file.read_text()).get("assets", {})
        aid_to_name = {v: k for k, v in assets.items()}

    # Step 2: indexed_asset_id → asset_id → clip name
    vid_to_name: dict[str, str] = {}
    for ia in client.indexes.indexed_assets.list(index_id=index_id):
        vid_to_name[ia.id] = aid_to_name.get(ia.asset_id, ia.asset_id[:12])

    results = client.search.query(
        index_id=index_id,
        query_text=query_text,
        search_options=["visual", "audio"],
        page_limit=max_results,
    )

    hits = []
    for item in results:
        hits.append(SearchHit(
            clip_name=vid_to_name.get(item.video_id, item.video_id[:12]),
            start=item.start or 0,
            end=item.end or 0,
            rank=item.rank or 0,
            transcript=(item.transcription or "").strip(),
        ))
        if len(hits) >= max_results:
            break

    return hits
