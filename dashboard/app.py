from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

st.set_page_config(
    page_title="RevLoop",
    page_icon="↻",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        .block-container {
            max-width: 1440px;
            padding-top: 2.5rem;
            padding-bottom: 4rem;
        }

        [data-testid="stMetric"] {
            border: 1px solid rgba(128, 128, 128, 0.22);
            border-radius: 14px;
            padding: 1rem 1.1rem;
            background: rgba(128, 128, 128, 0.035);
        }

        [data-testid="stMetricLabel"] {
            font-size: 0.85rem;
        }

        [data-testid="stMetricValue"] {
            font-size: 1.65rem;
        }

        div[data-testid="stExpander"] {
            border-radius: 10px;
        }

        section[data-testid="stSidebar"] {
            border-right: 1px solid rgba(128, 128, 128, 0.15);
        }

        .revloop-eyebrow {
            font-size: 0.78rem;
            font-weight: 650;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            opacity: 0.65;
            margin-bottom: 0.25rem;
        }

        .revloop-title {
            font-size: 2.25rem;
            font-weight: 750;
            line-height: 1.1;
            margin-bottom: 0.35rem;
        }

        .revloop-subtitle {
            font-size: 1rem;
            opacity: 0.68;
            margin-bottom: 1.5rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


pages = [
    st.Page(
        "pages/overview.py",
        title="Overview",
        icon=":material/dashboard:",
        default=True,
    ),
    st.Page(
        "pages/root_cause.py",
        title="Root Cause Analysis",
        icon=":material/analytics:",
    ),
    st.Page(
        "pages/case_explorer.py",
        title="Case Explorer",
        icon=":material/search:",
    ),
    st.Page(
        "pages/batch_runs.py",
        title="Batch Runs",
        icon=":material/history:",
    ),
]


page = st.navigation(
    pages,
    position="sidebar",
)

page.run()