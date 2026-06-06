import streamlit as st
import time
from typing import Dict

from models.agent import Agent
from services.llm_client import create_llm_client
from services.conversation import run_conversation_round
from services.memory import extract_and_store_facts, update_reflections
from simulation.engine import (
    SimulationState,
    run_simulation_step,
    run_full_simulation,
    group_agents_by_location,
)
from services.planning import generate_daily_plan
from config import LLMConfig, SimulationConfig


def _init_simulation_state():
    if "sim_state" not in st.session_state:
        st.session_state.sim_state = SimulationState()
    if "sim_logs" not in st.session_state:
        st.session_state.sim_logs = []


def render_simulation_panel(llm_config: LLMConfig, sim_config: SimulationConfig):
    _init_simulation_state()

    st.header("시뮬레이션 실행")

    agents = st.session_state.get("agents", {})

    if len(agents) < 2:
        st.warning("시뮬레이션을 실행하려면 최소 2명의 Agent가 필요합니다.")
        return

    st.subheader("수동 대화")
    st.caption("직접 참여 Agent, 발언 횟수, 주제를 지정하여 대화를 실행합니다.")

    agent_names = list(agents.keys())

    with st.form("manual_conv_form"):
        selected = st.multiselect(
            "참여 Agent 선택 (2명 이상)",
            options=agent_names,
            default=agent_names[:2] if len(agent_names) >= 2 else agent_names,
            key="manual_participants",
        )

        col1, col2 = st.columns(2)
        with col1:
            manual_turns = st.number_input(
                "발언 횟수", min_value=2, max_value=20, value=4, key="manual_turns"
            )
        with col2:
            manual_topic = st.text_input(
                "대화 주제 (비워두면 자동 생성)", key="manual_topic"
            )

        run_manual = st.form_submit_button("대화 실행", use_container_width=True)

    if run_manual:
        if len(selected) < 2:
            st.error("2명 이상의 Agent를 선택해주세요.")
        else:
            _run_manual_conversation(
                llm_config, agents, selected, manual_turns,
                manual_topic if manual_topic.strip() else None,
            )

    st.divider()

    st.subheader("전체 시뮬레이션")
    st.caption(
        f"{sim_config.total_days}일간, {sim_config.time_start}~{sim_config.time_end} 시간대별로 "
        f"자동 진행됩니다."
    )

    col_run, col_reset = st.columns([3, 1])
    with col_run:
        run_full = st.button(
            "전체 시뮬레이션 시작",
            type="primary",
            use_container_width=True,
            key="run_full_sim",
        )
    with col_reset:
        if st.button("상태 초기화", use_container_width=True, key="reset_sim"):
            st.session_state.sim_state = SimulationState()
            st.session_state.sim_logs = []
            st.rerun()

    if run_full:
        _run_full_simulation(llm_config, sim_config, agents)

    if st.session_state.sim_logs:
        st.subheader("진행 로그")
        log_container = st.container(height=300)
        with log_container:
            for log_entry in st.session_state.sim_logs:
                st.text(log_entry)

    sim_state: SimulationState = st.session_state.sim_state
    if sim_state.conversations:
        st.divider()
        st.subheader(f"대화 기록 ({len(sim_state.conversations)}건)")

        for conv in reversed(sim_state.conversations):
            label = (
                f"{conv.day}일차 {conv.time_slot} | {conv.location} | "
                f"{', '.join(conv.participants)}"
            )
            with st.expander(label):
                if conv.topic:
                    st.caption(f"주제: {conv.topic}")
                for msg in conv.messages:
                    st.markdown(f"**{msg['speaker']}:** {msg['content']}")


def _run_manual_conversation(
    llm_config: LLMConfig,
    agents: Dict[str, Agent],
    selected_names: list,
    turns: int,
    topic,
):
    try:
        llm = create_llm_client(llm_config)
    except Exception as e:
        st.error(f"LLM 클라이언트 생성 실패: {e}")
        return

    participants = [agents[name] for name in selected_names]
    sim_state: SimulationState = st.session_state.sim_state
    sim_state.round_counter += 1

    with st.spinner("대화 생성 중..."):
        conv = run_conversation_round(
            llm=llm,
            participants=participants,
            turns=turns,
            round_id=sim_state.round_counter,
            day=sim_state.current_day or 1,
            time_slot="수동",
            location="수동 대화",
            topic=topic,
        )
        sim_state.conversations.append(conv)

    with st.spinner("Fact 추출 중..."):
        extract_and_store_facts(llm, conv, agents)

    with st.spinner("Reflection 업데이트 중..."):
        update_reflections(llm, conv, agents)

    st.success("대화 및 메모리 업데이트 완료!")
    st.rerun()


def _run_full_simulation(
    llm_config: LLMConfig,
    sim_config: SimulationConfig,
    agents: Dict[str, Agent],
):
    try:
        llm = create_llm_client(llm_config)
    except Exception as e:
        st.error(f"LLM 클라이언트 생성 실패: {e}")
        return

    sim_state = SimulationState(agents=agents)
    st.session_state.sim_state = sim_state
    st.session_state.sim_logs = []

    progress_bar = st.progress(0)
    status_text = st.empty()
    log_area = st.container(height=400)

    time_slots = sim_config.get_time_slots()
    total_steps = sim_config.total_days * len(time_slots)
    current_step = 0

    def on_progress(msg: str):
        st.session_state.sim_logs.append(msg)
        with log_area:
            st.text(msg)

    for day in range(1, sim_config.total_days + 1):
        sim_state.current_day = day
        on_progress(f"{'='*50}")
        on_progress(f"  {day}일차 시작")
        on_progress(f"{'='*50}")

        status_text.text(f"{day}일차: Agent 일정 수립 중...")
        for agent in agents.values():
            agent.schedule = generate_daily_plan(
                llm, agent, sim_config.locations, time_slots, day
            )
            schedule_text = ", ".join(
                f"{t}: {l}" for t, l in sorted(agent.schedule.items())
            )
            on_progress(f"  {agent.name} 일정: {schedule_text}")

        for time_slot in time_slots:
            current_step += 1
            progress_bar.progress(current_step / total_steps)
            status_text.text(f"{day}일차 {time_slot} 진행 중...")

            sim_state.current_time_slot = time_slot
            run_simulation_step(llm, sim_state, sim_config, time_slot, day, on_progress)

        on_progress(f"  {day}일차 종료")

    sim_state.is_finished = True
    sim_state.is_running = False
    progress_bar.progress(1.0)
    status_text.text("시뮬레이션 완료!")
    st.success("시뮬레이션이 완료되었습니다. '리포트' 탭에서 결과를 확인하세요.")
