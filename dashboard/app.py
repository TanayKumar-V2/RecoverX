from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st

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
            padding-top: 2rem;
            padding-bottom: 3rem;
            max-width: 1400px;
        }

        [data-testid="stMetric"] {
            padding: 1rem;
            border: 1px solid rgba(128, 128, 128, 0.2);
            border-radius: 12px;
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