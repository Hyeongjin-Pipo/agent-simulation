import streamlit as st

from models.agent import Agent
from config import DEFAULT_AGENTS


def _init_agents_state():
    if "agents" not in st.session_state:
        st.session_state.agents = {}


def render_agent_panel():
    _init_agents_state()

    st.header("Agent 관리")

    col_preset, col_clear = st.columns([3, 1])
    with col_preset:
        if st.button("기본 Agent 불러오기", use_container_width=True, key="load_preset"):
            for preset in DEFAULT_AGENTS:
                agent = Agent(
                    name=preset["name"],
                    age=preset["age"],
                    job=preset["job"],
                    personality=preset["personality"],
                    memory=preset.get("initial_memory", {}),
                )
                st.session_state.agents[agent.name] = agent
            st.rerun()
    with col_clear:
        if st.button("전체 초기화", type="secondary", use_container_width=True, key="clear_agents"):
            st.session_state.agents = {}
            st.rerun()

    st.divider()

    with st.expander("새 Agent 추가", expanded=len(st.session_state.agents) == 0):
        with st.form("add_agent_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("이름", key="new_name")
                age = st.number_input("나이", min_value=1, max_value=100, value=25, key="new_age")
            with col2:
                job = st.text_input("직업", key="new_job")
                personality = st.text_input("성격", key="new_personality")

            initial_memory_text = st.text_area(
                "초기 Memory (선택, 한 줄에 하나씩: 대상이름|사실)",
                placeholder="이서연|카페를 운영하는 사람이라고 들었다\n박준호|같은 동네에 산다고 한다",
                key="new_memory",
                height=80,
            )

            submitted = st.form_submit_button("Agent 추가", use_container_width=True)
            if submitted:
                if not name or not job or not personality:
                    st.error("이름, 직업, 성격은 필수 항목입니다.")
                elif name in st.session_state.agents:
                    st.error(f"'{name}' 이름의 Agent가 이미 존재합니다.")
                else:
                    initial_memory = {}
                    if initial_memory_text.strip():
                        for line in initial_memory_text.strip().split("\n"):
                            if "|" in line:
                                parts = line.split("|", 1)
                                target = parts[0].strip()
                                fact = parts[1].strip()
                                if target not in initial_memory:
                                    initial_memory[target] = []
                                initial_memory[target].append(fact)

                    agent = Agent(
                        name=name, age=age, job=job,
                        personality=personality, memory=initial_memory,
                    )
                    st.session_state.agents[name] = agent
                    st.success(f"'{name}' Agent가 추가되었습니다.")
                    st.rerun()

    st.divider()

    if not st.session_state.agents:
        st.info("등록된 Agent가 없습니다. Agent를 추가하거나 기본 프리셋을 불러오세요.")
        return

    st.subheader(f"등록된 Agent ({len(st.session_state.agents)}명)")

    for name, agent in st.session_state.agents.items():
        with st.expander(f"{agent.name} ({agent.age}세, {agent.job})"):
            st.markdown(f"**성격:** {agent.personality}")

            if agent.memory:
                st.markdown("**Memory (알고 있는 사실):**")
                for target, facts in agent.memory.items():
                    st.markdown(f"*{target}에 대해:*")
                    for fact in facts:
                        st.markdown(f"- {fact}")
            else:
                st.caption("아직 기억하고 있는 사실이 없습니다.")

            if agent.relation_map:
                st.markdown("**Relation Map (관계 요약):**")
                for target, reflection in agent.relation_map.items():
                    st.markdown(f"*{target}:* {reflection}")

            if agent.schedule:
                st.markdown("**오늘의 일정:**")
                schedule_text = " / ".join(
                    f"{t}: {l}" for t, l in sorted(agent.schedule.items())
                )
                st.caption(schedule_text)

            if st.button(f"'{name}' 삭제", key=f"del_{name}"):
                del st.session_state.agents[name]
                st.rerun()
