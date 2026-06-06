import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st

from ui.sidebar import render_sidebar
from ui.agent_panel import render_agent_panel
from ui.simulation_panel import render_simulation_panel
from ui.report_panel import render_report_panel


def main():
    st.set_page_config(
        page_title="다중 에이전트 소셜 시뮬레이션",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("다중 에이전트 소셜 시뮬레이션")
    st.caption(
        "Agent들이 가상의 공간에서 자율적으로 대화하고, "
        "서로에 대한 기억과 관계를 형성하는 시뮬레이션입니다."
    )

    llm_config, sim_config = render_sidebar()

    tab_agent, tab_sim, tab_report = st.tabs([
        "Agent 관리",
        "시뮬레이션",
        "리포트",
    ])

    with tab_agent:
        render_agent_panel()

    with tab_sim:
        render_simulation_panel(llm_config, sim_config)

    with tab_report:
        render_report_panel()


if __name__ == "__main__":
    main()
