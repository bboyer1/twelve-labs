"""BWC-IQ Streamlit Dashboard.

Launch with:
    streamlit run app.py
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

# ---------------------------------------------------------------------------
# Paths & constants
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent
OUTPUTS_DIR = REPO_ROOT / "outputs"
CLIPS_DIR = REPO_ROOT / "clips"
PROMPTS_DIR = REPO_ROOT / "prompts"
INDEXES_FILE = OUTPUTS_DIR / "indexes.json"

PRIORITY_COLORS = {"Urgent": "#dc2626", "Standard": "#ca8a04", "Archive": "#6b7280"}
UOF_COLORS = {
    "lethal_force": "#dc2626",
    "less_lethal": "#ea580c",
    "physical_restraint": "#ca8a04",
    "verbal_command": "#ca8a04",
    "none": "#16a34a",
}

# Friendly display names for clips
CLIP_LABELS: dict[str, str] = {
    "clip_01_nypd_107pct_ois_20260126": "NYPD 107th Pct OIS (01/26/2026)",
    "clip_02_lapd_armed_suspect_restraining_order": "LAPD Armed Suspect / Restraining Order",
    "clip_03_kalamazoo_dps_traffic_stop": "Kalamazoo DPS Traffic Stop",
    "clip_04_nmsp_dwi_stop": "NM State Police DWI Stop",
    "clip_non-body-cam": "Non-Body-Cam (Control Clip)",
}

# Known clip durations in seconds (from source metadata)
CLIP_DURATIONS: dict[str, int] = {
    "clip_01_nypd_107pct_ois_20260126": 768,       # 12:48
    "clip_02_lapd_armed_suspect_restraining_order": 443,  # 7:23
    "clip_03_kalamazoo_dps_traffic_stop": 159,      # 2:39
    "clip_04_nmsp_dwi_stop": 141,                   # 2:21
    "clip_non-body-cam": 30,                        # ~0:30
}

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


@st.cache_data
def load_reports() -> dict[str, dict]:
    """Load all report.json files from outputs/."""
    reports: dict[str, dict] = {}
    for d in sorted(OUTPUTS_DIR.iterdir()):
        rpath = d / "report.json"
        if d.is_dir() and rpath.exists():
            reports[d.name] = json.loads(rpath.read_text())
    return reports


@st.cache_data
def load_indexes() -> dict:
    if INDEXES_FILE.exists():
        return json.loads(INDEXES_FILE.read_text())
    return {}


def badge_html(text: str, color: str) -> str:
    return (
        f'<span style="background:{color};color:white;padding:3px 10px;'
        f'border-radius:12px;font-weight:600;font-size:0.85rem;">{text}</span>'
    )


def parse_timestamp_seconds(ts: str) -> float | None:
    """Parse Pegasus timestamp (MM:SS:FF or HH:MM:SS) to total seconds.

    Pegasus uses MM:SS:FF format (minutes:seconds:frames) despite the
    prompt requesting HH:MM:SS. We treat the first field as minutes.
    """
    parts = ts.strip().split(":")
    try:
        if len(parts) == 3:
            return int(parts[0]) * 60 + int(parts[1])
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
    except ValueError:
        return None
    return None


def format_duration(seconds: int) -> str:
    m, s = divmod(seconds, 60)
    return f"{m}:{s:02d}"


def format_filesize(b: int) -> str:
    if b > 1_000_000:
        return f"{b / 1_000_000:.1f} MB"
    return f"{b / 1_000:.1f} KB"


# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="BWC-IQ Dashboard",
    page_icon=":shield:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Hide Streamlit chrome for a cleaner demo
st.markdown(
    """<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

st.sidebar.markdown(
    '<h1 style="margin-bottom:0;">BWC-IQ</h1>'
    '<p style="margin-top:0;color:#8899aa;font-size:0.85rem;">'
    'Body-Worn Camera Intelligence<br>'
    '<span style="font-size:0.75rem;">Powered by TwelveLabs Pegasus 1.2 &amp; Marengo 3.0</span>'
    '</p>',
    unsafe_allow_html=True,
)
st.sidebar.divider()

page = st.sidebar.radio(
    "Navigate",
    ["About", "Dashboard", "Clip Detail", "Cross-Library Search"],
    label_visibility="collapsed",
)
st.sidebar.divider()
st.sidebar.caption("Bret Boyer | TwelveLabs SE Exercise")

reports = load_reports()
indexes = load_indexes()

# ---------------------------------------------------------------------------
# Dashboard page
# ---------------------------------------------------------------------------

if page == "Dashboard":
    st.markdown("# Analyst Queue")
    st.caption(
        "Clips sorted by priority. Urgent clips require supervisor review within 24 hours."
    )

    # Summary metrics
    priorities = [r["triage"]["priority"] for r in reports.values()]
    cols = st.columns(4)
    cols[0].metric("Total Clips", len(reports))
    cols[1].metric("Urgent", priorities.count("Urgent"))
    cols[2].metric("Standard", priorities.count("Standard"))
    cols[3].metric("Archive", priorities.count("Archive"))

    # --- Charts ---
    chart_left, chart_right = st.columns(2)

    # Priority distribution
    with chart_left:
        priority_df = pd.DataFrame(
            {"Priority": priorities}
        ).groupby("Priority").size().reset_index(name="Count")
        # Sort by severity — inverted so Urgent is at the bottom (visually prominent)
        p_order = {"Urgent": 2, "Standard": 1, "Archive": 0}
        priority_df["_sort"] = priority_df["Priority"].map(p_order)
        priority_df = priority_df.sort_values("_sort").drop(columns="_sort")

        st.markdown("#### Priority Distribution")
        st.bar_chart(priority_df, x="Priority", y="Count", color="Priority",
                     horizontal=True, height=200)

    # Event type frequency across all clips
    with chart_right:
        all_events = []
        for r in reports.values():
            for ev in r["triage"].get("events", []):
                all_events.append(ev.get("type", "unknown"))
        if all_events:
            event_df = pd.DataFrame(
                {"Event": all_events}
            ).groupby("Event").size().reset_index(name="Count")
            event_df = event_df.sort_values("Count", ascending=False).head(10)

            st.markdown("#### Top Event Types")
            st.bar_chart(event_df, x="Event", y="Count", horizontal=True,
                         height=200)

    st.divider()

    # Sort: Urgent first, then Standard, then Archive
    priority_order = {"Urgent": 0, "Standard": 1, "Archive": 2}
    sorted_clips = sorted(
        reports.items(),
        key=lambda kv: priority_order.get(kv[1]["triage"]["priority"], 9),
    )

    for clip_name, report in sorted_clips:
        t = report["triage"]
        c = report["compliance"]
        priority = t["priority"]
        uof_type = c.get("use_of_force", {}).get("type", "none")
        events = t.get("events", [])
        label = CLIP_LABELS.get(clip_name, clip_name)
        p_color = PRIORITY_COLORS.get(priority, "#374151")
        u_color = UOF_COLORS.get(uof_type, "#374151")

        with st.container():
            left, mid, right = st.columns([4, 3, 2])

            with left:
                st.markdown(
                    f"**{label}**  \n"
                    f"{badge_html(priority, p_color)} "
                    f"{badge_html(uof_type.replace('_', ' '), u_color)}",
                    unsafe_allow_html=True,
                )

            with mid:
                reasoning_preview = t.get("reasoning", "")[:160]
                if len(t.get("reasoning", "")) > 160:
                    reasoning_preview += "..."
                st.caption(reasoning_preview)

            with right:
                st.markdown(
                    f"**{len(events)}** events  \n"
                    f"`{report['generated_at'][:10]}`"
                )

            st.divider()

# ---------------------------------------------------------------------------
# Clip Detail page
# ---------------------------------------------------------------------------

elif page == "Clip Detail":
    clip_options = list(reports.keys())
    display_options = [CLIP_LABELS.get(c, c) for c in clip_options]

    selected_idx = st.sidebar.selectbox(
        "Select clip",
        range(len(clip_options)),
        format_func=lambda i: display_options[i],
    )
    clip_name = clip_options[selected_idx]
    report = reports[clip_name]

    t = report["triage"]
    c = report["compliance"]
    src = report["source"]
    tl = report["twelvelabs"]

    priority = t["priority"]
    uof = c.get("use_of_force", {})
    uof_type = uof.get("type", "none")
    p_color = PRIORITY_COLORS.get(priority, "#374151")
    u_color = UOF_COLORS.get(uof_type, "#374151")

    # Header
    st.markdown(f"# {CLIP_LABELS.get(clip_name, clip_name)}")
    st.markdown(
        f"{badge_html(priority, p_color)}&ensp;"
        f"{badge_html(uof_type.replace('_', ' '), u_color)}",
        unsafe_allow_html=True,
    )

    # AI notice
    st.info(
        "This report was generated by AI (Pegasus 1.2) and is intended "
        "for human review, not as a final determination.",
        icon="\u26a0\ufe0f",
    )

    # --- Triage section ---
    st.markdown("## Triage Classification")

    triage_prompt_ver = t.get("_prompt_version", "v1")
    with st.expander("Pegasus API Call -- Triage"):
        st.code(
            f"""from twelvelabs import TwelveLabs
from twelvelabs.types import ResponseFormat, VideoContext_AssetId

client = TwelveLabs(api_key="***")

prompt = open("prompts/triage.{triage_prompt_ver}.md").read()
schema = json.load(open("schemas/triage.{triage_prompt_ver}.json"))

result = client.analyze(
    video=VideoContext_AssetId(asset_id="{tl['asset_id']}"),
    prompt=prompt,
    response_format=ResponseFormat(
        type="json_schema",
        json_schema=schema,
    ),
    max_tokens=2048,
)""",
            language="python",
        )

    st.markdown(f"**Priority: {priority}**")
    st.markdown(f">{t.get('reasoning', '')}")

    events = t.get("events", [])
    if events:
        st.markdown("### Flagged Events")
        for ev in events:
            conf = ev.get("confidence", 0)
            ts = ev.get("timestamp", "?")
            etype = ev.get("type", "?")
            bar_pct = int(conf * 100)
            st.markdown(
                f"- `{ts}` **{etype}** "
                f"<span style='display:inline-block;width:60px;height:8px;"
                f"background:#e2e8f0;border-radius:4px;vertical-align:middle;'>"
                f"<span style='display:block;width:{bar_pct}%;height:100%;"
                f"background:#3b82f6;border-radius:4px;'></span></span> "
                f"<span style='color:#64748b;font-size:0.85rem;'>{conf:.0%}</span>",
                unsafe_allow_html=True,
            )

    # --- Compliance section ---
    st.markdown("## Policy Compliance")

    compliance_prompt_ver = c.get("_prompt_version", "v1")
    with st.expander("Pegasus API Call -- Compliance"):
        st.code(
            f"""from twelvelabs import TwelveLabs
from twelvelabs.types import ResponseFormat, VideoContext_AssetId

client = TwelveLabs(api_key="***")

prompt = open("prompts/compliance.{compliance_prompt_ver}.md").read()
schema = json.load(open("schemas/compliance.{compliance_prompt_ver}.json"))

result = client.analyze(
    video=VideoContext_AssetId(asset_id="{tl['asset_id']}"),
    prompt=prompt,
    response_format=ResponseFormat(
        type="json_schema",
        json_schema=schema,
    ),
    max_tokens=4096,
)""",
            language="python",
        )

    comp_cols = st.columns(2)

    # Miranda
    miranda = c.get("miranda", {})
    with comp_cols[0]:
        st.markdown("### Miranda Rights")
        if miranda.get("delivered"):
            st.success("Delivered", icon="\u2705")
            if miranda.get("timestamp"):
                st.caption(f"At {miranda['timestamp']}")
            if miranda.get("quote"):
                st.caption(f'"{miranda["quote"]}"')
        else:
            st.markdown(
                "<span style='color:#6b7280;'>Not delivered</span>",
                unsafe_allow_html=True,
            )

    # Use of force
    with comp_cols[1]:
        st.markdown("### Use of Force")
        st.markdown(
            badge_html(uof_type.replace("_", " "), u_color),
            unsafe_allow_html=True,
        )
        uof_ts = uof.get("timestamp", "")
        if uof_ts and uof_ts.strip(":0"):
            st.caption(f"At {uof_ts}")
        if uof.get("description"):
            st.caption(uof["description"])

    # Positioning
    positioning = c.get("positioning", {})
    if positioning.get("assessment"):
        st.markdown("### Officer Positioning")
        st.markdown(positioning["assessment"])

    # De-escalation
    deesc = c.get("deescalation", [])
    if deesc:
        st.markdown("### De-escalation Instances")
        for d in deesc:
            quote_str = f' -- *"{d.get("quote", "")}"*' if d.get("quote") else ""
            st.markdown(
                f"- `{d.get('timestamp', '?')}` **{d.get('technique', '?')}**{quote_str}"
            )

    # Compliance reasoning
    st.markdown("### Compliance Summary")
    st.warning(c.get("reasoning", ""), icon="\u270d")

    # --- Chain of Custody ---
    st.markdown("## Chain of Custody")
    coc_cols = st.columns(2)
    with coc_cols[0]:
        st.markdown(f"**SHA-256**  \n`{src['sha256']}`")
        st.markdown(f"**File size**  \n{format_filesize(src['bytes'])}")
        st.markdown(f"**Asset ID**  \n`{tl['asset_id']}`")
    with coc_cols[1]:
        st.markdown(f"**Model**  \n`{tl['model']}`")
        st.markdown(
            f"**Triage prompt**  \n`triage.{t.get('_prompt_version', '?')}`"
        )
        st.markdown(
            f"**Compliance prompt**  \n`compliance.{c.get('_prompt_version', '?')}`"
        )
        st.markdown(f"**Generated**  \n`{report['generated_at']}`")

    # Raw JSON expander
    with st.expander("Raw JSON"):
        st.json(report)

    # --- Re-analyze & Compare ---
    st.markdown("## Re-analyze & Compare")

    clip_dur = CLIP_DURATIONS.get(clip_name)
    dur_label = f" (clip duration: **{format_duration(clip_dur)}**)" if clip_dur else ""
    st.caption(
        "Re-run Pegasus on this clip and compare the new output against the "
        f"saved report. Useful for evaluating model consistency.{dur_label}"
    )

    def _render_event(ev: dict, duration: int | None) -> str:
        """Render one event line, flagging timestamps past clip end."""
        ts = ev.get("timestamp", "?")
        etype = ev.get("type", "?")
        conf = ev.get("confidence", 0)
        ts_sec = parse_timestamp_seconds(ts)
        flag = ""
        if duration and ts_sec is not None and ts_sec > duration:
            flag = " :red[past clip end]"
        return f"- `{ts}` **{etype}** ({conf:.0%}){flag}"

    rerun_col1, rerun_col2 = st.columns(2)
    run_triage = rerun_col1.button("Re-run Triage")
    run_compliance = rerun_col2.button("Re-run Compliance")

    # Persist re-run results in session state keyed by clip
    triage_key = f"rerun_triage_{clip_name}"
    compliance_key = f"rerun_compliance_{clip_name}"

    if run_triage:
        with st.spinner("Running triage via Pegasus..."):
            try:
                from src.triage import triage as run_triage_fn

                st.session_state[triage_key] = run_triage_fn(tl["asset_id"])
            except Exception as e:
                st.error(f"Triage failed: {e}")

    if run_compliance:
        with st.spinner("Running compliance via Pegasus..."):
            try:
                from src.compliance import compliance as run_compliance_fn

                st.session_state[compliance_key] = run_compliance_fn(tl["asset_id"])
            except Exception as e:
                st.error(f"Compliance failed: {e}")

    # --- Triage comparison ---
    if triage_key in st.session_state:
        new_t = st.session_state[triage_key]
        st.markdown("### Triage Comparison")

        old_col, new_col = st.columns(2)
        old_priority = t.get("priority", "?")
        new_priority = new_t.get("priority", "?")
        old_p_color = PRIORITY_COLORS.get(old_priority, "#374151")
        new_p_color = PRIORITY_COLORS.get(new_priority, "#374151")

        with old_col:
            st.markdown("**Saved**")
            st.markdown(badge_html(old_priority, old_p_color), unsafe_allow_html=True)
            st.markdown(f"**{len(t.get('events', []))}** events")
            st.caption(t.get("reasoning", ""))
            with st.expander("Saved events"):
                for ev in t.get("events", []):
                    st.markdown(_render_event(ev, clip_dur))

        with new_col:
            st.markdown("**New run**")
            st.markdown(badge_html(new_priority, new_p_color), unsafe_allow_html=True)
            st.markdown(f"**{len(new_t.get('events', []))}** events")
            st.caption(new_t.get("reasoning", ""))
            with st.expander("New events"):
                for ev in new_t.get("events", []):
                    st.markdown(_render_event(ev, clip_dur))

        # Count out-of-range timestamps
        def _count_oor(events: list[dict], dur: int | None) -> int:
            if not dur:
                return 0
            return sum(
                1 for e in events
                if (s := parse_timestamp_seconds(e.get("timestamp", ""))) is not None
                and s > dur
            )

        old_oor = _count_oor(t.get("events", []), clip_dur)
        new_oor = _count_oor(new_t.get("events", []), clip_dur)

        # Highlight differences
        changed = []
        if old_priority != new_priority:
            changed.append(f"Priority: {old_priority} -> {new_priority}")
        old_event_types = sorted(ev.get("type", "") for ev in t.get("events", []))
        new_event_types = sorted(ev.get("type", "") for ev in new_t.get("events", []))
        added = set(new_event_types) - set(old_event_types)
        removed = set(old_event_types) - set(new_event_types)
        if added:
            changed.append(f"New event types: {', '.join(sorted(added))}")
        if removed:
            changed.append(f"Removed event types: {', '.join(sorted(removed))}")
        if old_oor or new_oor:
            changed.append(
                f"Timestamps past clip end: saved={old_oor}, new={new_oor}"
            )

        if changed:
            st.warning("**Differences:** " + " | ".join(changed))
        else:
            st.success("No material differences in classification.")

    # --- Compliance comparison ---
    if compliance_key in st.session_state:
        new_c = st.session_state[compliance_key]
        st.markdown("### Compliance Comparison")

        old_col, new_col = st.columns(2)
        old_uof = c.get("use_of_force", {}).get("type", "none")
        new_uof = new_c.get("use_of_force", {}).get("type", "none")
        old_u_color = UOF_COLORS.get(old_uof, "#374151")
        new_u_color = UOF_COLORS.get(new_uof, "#374151")

        with old_col:
            st.markdown("**Saved**")
            st.markdown(
                f"UoF: {badge_html(old_uof.replace('_', ' '), old_u_color)}"
                f"&ensp;Miranda: {'delivered' if c.get('miranda', {}).get('delivered') else 'no'}",
                unsafe_allow_html=True,
            )
            st.markdown(f"**{len(c.get('deescalation', []))}** de-escalation instances")
            st.caption(c.get("reasoning", ""))

        with new_col:
            st.markdown("**New run**")
            st.markdown(
                f"UoF: {badge_html(new_uof.replace('_', ' '), new_u_color)}"
                f"&ensp;Miranda: {'delivered' if new_c.get('miranda', {}).get('delivered') else 'no'}",
                unsafe_allow_html=True,
            )
            st.markdown(f"**{len(new_c.get('deescalation', []))}** de-escalation instances")
            st.caption(new_c.get("reasoning", ""))

        # Highlight differences
        changed = []
        if old_uof != new_uof:
            changed.append(f"Use of force: {old_uof} -> {new_uof}")
        old_miranda = c.get("miranda", {}).get("delivered", False)
        new_miranda = new_c.get("miranda", {}).get("delivered", False)
        if old_miranda != new_miranda:
            changed.append(f"Miranda: {old_miranda} -> {new_miranda}")
        old_deesc_count = len(c.get("deescalation", []))
        new_deesc_count = len(new_c.get("deescalation", []))
        if old_deesc_count != new_deesc_count:
            changed.append(f"De-escalation instances: {old_deesc_count} -> {new_deesc_count}")

        if changed:
            st.warning("**Differences:** " + " | ".join(changed))
        else:
            st.success("No material differences in classification.")

# ---------------------------------------------------------------------------
# Cross-Library Search page
# ---------------------------------------------------------------------------

elif page == "Cross-Library Search":
    st.markdown("# Cross-Library Search")
    st.caption(
        "Natural-language queries across all indexed BWC footage via Marengo 3.0."
    )

    marengo_index_id = indexes.get("marengo_index_id")

    if not marengo_index_id:
        st.error("No Marengo index found. Run the indexing pipeline first.")
    else:
        example_queries = [
            "officer drew a firearm",
            "suspect was handcuffed",
            "de-escalation verbal commands",
            "traffic stop with vehicle search",
            "medical aid administered",
        ]

        st.markdown(
            "**Example queries:** "
            + " | ".join(f"`{q}`" for q in example_queries)
        )

        query_text = st.text_input(
            "Search query",
            placeholder="e.g. officer drew a firearm during a vehicle stop",
        )
        max_results = st.slider("Max results", 1, 10, 5)

        if query_text:
            # Show the API call being made
            with st.expander("Marengo API Call", expanded=True):
                st.code(
                    f"""from twelvelabs import TwelveLabs

client = TwelveLabs(api_key="***")

results = client.search.query(
    index_id="{marengo_index_id}",
    query_text="{query_text}",
    search_options=["visual", "audio"],
    page_limit={max_results},
)""",
                    language="python",
                )

            with st.spinner("Searching..."):
                try:
                    from src.search import query as search_query

                    hits = search_query(
                        marengo_index_id, query_text, max_results=max_results
                    )
                except Exception as e:
                    st.error(f"Search failed: {e}")
                    hits = []

            if not hits:
                st.info("No results found.")
            else:
                st.markdown(f"**{len(hits)} result(s)**")
                for hit in hits:
                    rank_icon = "\u2b50" if hit.rank == 1 else ""
                    label = CLIP_LABELS.get(hit.clip_name, hit.clip_name)
                    with st.container():
                        left, right = st.columns([1, 4])
                        with left:
                            st.markdown(f"### {rank_icon} #{hit.rank}")
                            st.code(hit.timestamp)
                        with right:
                            st.markdown(f"**{label}**")
                            if hit.transcript:
                                st.caption(f'"{hit.transcript}"')
                        st.divider()

# ---------------------------------------------------------------------------
# About page
# ---------------------------------------------------------------------------

elif page == "About":
    st.markdown("# About BWC-IQ")

    st.markdown(
        "BWC-IQ is a TwelveLabs-powered pipeline for automated body-worn camera "
        "footage triage and policy compliance auditing, built for the "
        "**TwelveLabs Solutions Engineering Take-Home Exercise** (Public Sector: "
        "Government Video Intelligence)."
    )

    # Architecture diagram
    st.markdown("### Architecture")
    arch_img = REPO_ROOT / "docs" / "architecture.png"
    if arch_img.exists():
        st.image(str(arch_img), use_container_width=True)
    else:
        st.caption("Architecture diagram not found at docs/architecture.png.")

    st.markdown(
        """
### Capabilities

1. **Triage Classification** (Pegasus 1.2) -- Urgent / Standard / Archive,
   with timestamped evidence and reasoning.
2. **Policy Compliance Audit** (Pegasus 1.2) -- Miranda delivery,
   de-escalation language, use-of-force type, officer-subject positioning.
3. **Cross-Library Search** (Marengo 3.0) -- Natural-language queries across
   the full video library.

### Public Sector Constraints Addressed

- **Data Sovereignty & Chain of Custody** -- TwelveLabs on Amazon Bedrock;
  SHA-256 hashes, asset IDs, and versioned prompts in every report.
- **Explainability** -- Every flag anchored to a timestamp, every call cites
  a versioned prompt, every report includes a reasoning narrative.
"""
    )

    st.markdown("### Prompt Versions")
    prompt_cols = st.columns(2)
    for i, name in enumerate(["triage", "compliance"]):
        pfile = PROMPTS_DIR / f"{name}.v1.md"
        if pfile.exists():
            with prompt_cols[i]:
                with st.expander(f"{name}.v1.md"):
                    st.code(pfile.read_text(), language="markdown")

    st.markdown("### Indexed Assets")
    if indexes:
        st.json(indexes)
    else:
        st.caption("No indexes.json found.")

    st.divider()
    st.caption(
        "Built by Bret Boyer | Powered by TwelveLabs Pegasus 1.2 & Marengo 3.0"
    )
