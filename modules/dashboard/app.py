"""
YouTube Shorts OS — Streamlit Control Panel

Run with: streamlit run modules/dashboard/app.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import json
from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from db.connection import fetchall, fetchone, execute
from modules.ideas.idea_generator import backlog_count
from modules.scripts.script_generator import approve_script, reject_script, get_scripts_pending_review

st.set_page_config(
    page_title="Shorts OS",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Sidebar navigation ─────────────────────────────────────────────────────
page = st.sidebar.selectbox(
    "Navigation",
    ["Overview", "Idea Backlog", "Script Review", "Publish Queue", "Analytics", "Experiments"],
)

st.sidebar.divider()
st.sidebar.caption("YouTube Shorts OS v1")


# ── Helper: colored metric ──────────────────────────────────────────────────
def status_badge(status: str) -> str:
    colors = {
        "backlog": "🔵", "approved": "🟢", "scripted": "🟡",
        "rejected": "🔴", "draft": "⚪", "live": "🟢",
        "queued": "🔵", "uploading": "🟡", "failed": "🔴",
    }
    return f"{colors.get(status, '⚫')} {status}"


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
if page == "Overview":
    st.title("Shorts OS — Overview")

    # KPI row
    col1, col2, col3, col4, col5 = st.columns(5)

    backlog = backlog_count()
    pending_scripts = len(get_scripts_pending_review())

    live_count = fetchone("SELECT COUNT(*) as n FROM publish_queue WHERE upload_status = 'live'")
    live_count = live_count["n"] if live_count else 0

    queued_count = fetchone("SELECT COUNT(*) as n FROM publish_queue WHERE upload_status IN ('queued','approved')")
    queued_count = queued_count["n"] if queued_count else 0

    avg_score = fetchone("SELECT AVG(performance_score) as s FROM performance_snapshots")
    avg_score = round(avg_score["s"] or 0, 2) if avg_score else 0

    col1.metric("Idea Backlog", backlog, help="Ideas in backlog/approved status")
    col2.metric("Scripts to Review", pending_scripts, help="Draft scripts awaiting approval")
    col3.metric("Videos Live", live_count)
    col4.metric("In Upload Queue", queued_count)
    col5.metric("Avg Perf Score", f"{avg_score:.2f}", help="0.0–1.0 composite score")

    st.divider()

    # Recent jobs
    st.subheader("Recent Jobs")
    jobs = fetchall(
        "SELECT job_type, status, created_at, error_message FROM jobs ORDER BY created_at DESC LIMIT 15"
    )
    if jobs:
        df = pd.DataFrame([dict(j) for j in jobs])
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No jobs yet.")

    # Top performing topics
    st.subheader("Top Topic Clusters")
    patterns = fetchall(
        """
        SELECT pattern_name, success_rate, avg_view_count, sample_size
        FROM content_patterns
        WHERE pattern_type = 'topic_cluster' AND sample_size > 0
        ORDER BY success_rate DESC
        """
    )
    if patterns:
        df = pd.DataFrame([dict(p) for p in patterns])
        fig = px.bar(df, x="pattern_name", y="success_rate",
                     color="avg_view_count", title="Topic Cluster Success Rate",
                     color_continuous_scale="Blues")
        st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: IDEA BACKLOG
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Idea Backlog":
    st.title("Idea Backlog")

    col1, col2 = st.columns([3, 1])
    with col2:
        status_filter = st.selectbox("Filter by status", ["all", "backlog", "approved", "rejected"])

    query = "SELECT * FROM ideas"
    if status_filter != "all":
        ideas = fetchall(f"{query} WHERE status = ? ORDER BY predicted_score DESC", (status_filter,))
    else:
        ideas = fetchall(f"{query} ORDER BY predicted_score DESC")

    if not ideas:
        st.info("No ideas yet. Run the idea generator to populate the backlog.")
    else:
        for idea in ideas:
            idea = dict(idea)
            with st.expander(f"{status_badge(idea['status'])} | {idea['title']} (score: {idea['predicted_score']:.2f})"):
                col1, col2 = st.columns(2)
                col1.write(f"**Topic cluster**: {idea['topic_cluster']}")
                col1.write(f"**Hook style**: {idea['hook_style']}")
                col1.write(f"**Emotional trigger**: {idea['emotional_trigger']}")
                col2.write(f"**Hook angle**: {idea['hook_angle']}")
                col2.write(f"**Why watch**: {idea['why_watch']}")

                if idea["status"] == "backlog":
                    c1, c2 = st.columns(2)
                    if c1.button("Approve", key=f"approve_idea_{idea['id']}"):
                        execute("UPDATE ideas SET status = 'approved' WHERE id = ?", (idea["id"],))
                        st.rerun()
                    if c2.button("Reject", key=f"reject_idea_{idea['id']}"):
                        execute("UPDATE ideas SET status = 'rejected' WHERE id = ?", (idea["id"],))
                        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: SCRIPT REVIEW
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Script Review":
    st.title("Script Review")

    scripts = get_scripts_pending_review()
    if not scripts:
        st.success("No scripts pending review.")
    else:
        for script in scripts:
            with st.expander(f"Script #{script['id']} — {script['idea_title']}"):
                st.markdown(f"**Hook**: {script['hook_text']}")
                st.markdown("**Full script:**")
                st.text_area("", value=script["full_script"], height=200, key=f"script_text_{script['id']}", disabled=True)
                st.markdown(f"**Visual notes**: {script['visual_notes']}")
                st.markdown(f"**Music mood**: {script['music_mood']}")
                st.caption(f"Est. duration: {script['estimated_duration']}s | Words: {script['word_count']}")

                # Hook variants
                variants = fetchall(
                    "SELECT * FROM hook_variants WHERE script_id = ?", (script["id"],)
                )
                if variants:
                    st.markdown("**Hook variants:**")
                    for v in variants:
                        st.markdown(f"- **{v['style']}**: {v['text']}")

                col1, col2, col3 = st.columns(3)
                if col1.button("Approve", key=f"approve_{script['id']}"):
                    approve_script(script["id"])
                    st.rerun()
                if col2.button("Reject", key=f"reject_{script['id']}"):
                    reject_script(script["id"], "Rejected via dashboard")
                    st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: PUBLISH QUEUE
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Publish Queue":
    st.title("Publish Queue")

    queue = fetchall(
        """
        SELECT pq.*, pr.video_path, pr.duration_actual
        FROM publish_queue pq
        JOIN productions pr ON pr.id = pq.production_id
        ORDER BY pq.created_at DESC
        LIMIT 30
        """
    )

    if not queue:
        st.info("No videos in queue yet.")
    else:
        for entry in queue:
            entry = dict(entry)
            with st.expander(f"{status_badge(entry['upload_status'])} | {entry['title']}"):
                col1, col2 = st.columns(2)
                col1.write(f"**Scheduled**: {entry.get('scheduled_for', 'Not set')}")
                col1.write(f"**YouTube URL**: {entry.get('youtube_url', '—')}")
                col2.write(f"**Duration**: {entry.get('duration_actual', 0):.1f}s")
                col2.write(f"**Video path**: {entry.get('video_path', '—')}")
                st.write(f"**Description**: {entry['description'][:200]}...")
                tags = json.loads(entry.get("hashtags", "[]"))
                st.write(f"**Hashtags**: {' '.join(tags)}")

                if entry["upload_status"] == "queued":
                    if st.button("Approve for upload", key=f"approve_upload_{entry['id']}"):
                        execute(
                            "UPDATE publish_queue SET upload_status = 'approved' WHERE id = ?",
                            (entry["id"],),
                        )
                        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: ANALYTICS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Analytics":
    st.title("Analytics")

    # Performance over time
    snapshots = fetchall(
        """
        SELECT ps.snapshot_date, ps.views, ps.avg_view_pct, ps.performance_score,
               pq.title
        FROM performance_snapshots ps
        JOIN publish_queue pq ON pq.id = ps.publish_queue_id
        ORDER BY ps.snapshot_date DESC
        LIMIT 200
        """
    )

    if not snapshots:
        st.info("No analytics data yet. Run the analytics ingester after videos go live.")
    else:
        df = pd.DataFrame([dict(s) for s in snapshots])
        df["snapshot_date"] = pd.to_datetime(df["snapshot_date"])

        col1, col2 = st.columns(2)
        with col1:
            fig = px.line(df.groupby("snapshot_date")["views"].sum().reset_index(),
                          x="snapshot_date", y="views", title="Daily Views")
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = px.box(df, x="snapshot_date", y="avg_view_pct",
                         title="Retention Distribution Over Time")
            st.plotly_chart(fig, use_container_width=True)

        # Top performers table
        st.subheader("Top Performers")
        top = df.groupby("title").agg(
            total_views=("views", "sum"),
            avg_retention=("avg_view_pct", "mean"),
            avg_score=("performance_score", "mean"),
        ).sort_values("avg_score", ascending=False).head(10)
        st.dataframe(top, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: EXPERIMENTS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Experiments":
    st.title("Experiments")

    experiments = fetchall("SELECT * FROM experiments ORDER BY created_at DESC")
    if not experiments:
        st.info("No experiments yet.")
    else:
        for exp in experiments:
            exp = dict(exp)
            with st.expander(f"{exp['name']} — {exp['status']}"):
                st.write(f"**Variable**: {exp['variable']}")
                st.write(f"**Hypothesis**: {exp['hypothesis']}")
                st.write(f"**Control**: {exp['control_value']} | **Test**: {exp['test_value']}")
                if exp.get("result_summary"):
                    st.success(f"Result: {exp['result_summary']}")
                    st.write(f"**Winner**: {exp.get('winner', '—')}")
