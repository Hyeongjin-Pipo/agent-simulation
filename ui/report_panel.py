import streamlit as st
import os

from models.agent import Agent
from services.report import generate_report_text, save_report_to_file


def render_report_panel():
    st.header("리포트")

    agents = st.session_state.get("agents", {})

    if not agents:
        st.info("Agent가 등록되지 않았습니다.")
        return

    agent_names = list(agents.keys())
    selected_name = st.selectbox(
        "리포트 대상 Agent 선택",
        options=agent_names,
        key="report_agent",
    )

    if not selected_name:
        return

    agent: Agent = agents[selected_name]

    col_gen, col_save = st.columns([3, 1])

    with col_gen:
        generate_btn = st.button(
            "리포트 생성",
            type="primary",
            use_container_width=True,
            key="gen_report",
        )

    with col_save:
        save_btn = st.button(
            "파일로 저장",
            use_container_width=True,
            key="save_report",
        )

    st.divider()

    if generate_btn or "current_report" in st.session_state:
        report_text = generate_report_text(agent, agents)
        st.session_state.current_report = report_text
        st.session_state.current_report_agent = selected_name

    if "current_report" in st.session_state:
        st.text(st.session_state.current_report)

        st.download_button(
            label="리포트 다운로드 (.md)",
            data=st.session_state.current_report,
            file_name=f"report_{st.session_state.get('current_report_agent', 'agent')}.md",
            mime="text/markdown",
            use_container_width=True,
        )

    if save_btn:
        report_text = generate_report_text(agent, agents)
        filepath = save_report_to_file(agent, agents, output_dir="reports")
        st.success(f"리포트가 저장되었습니다: {filepath}")

    st.divider()

    st.subheader("전체 Agent 상태 요약")

    for name, ag in agents.items():
        with st.expander(f"{ag.name} ({ag.age}세, {ag.job})"):
            if ag.met_agents:
                st.markdown(f"**만난 사람:** {', '.join(ag.met_agents)}")
            else:
                st.caption("아직 만난 사람이 없습니다.")

            total_facts = sum(len(facts) for facts in ag.memory.values())
            st.markdown(f"**기억 중인 사실:** {total_facts}건")

            if ag.relation_map:
                st.markdown("**관계 요약:**")
                for target, reflection in ag.relation_map.items():
                    st.markdown(f"- **{target}:** {reflection}")
