import streamlit as st

from config import LLMConfig, SimulationConfig


def render_sidebar() -> tuple:
    st.sidebar.title("시뮬레이션 설정")

    st.sidebar.subheader("LLM 백엔드")

    backend = st.sidebar.radio(
        "사용할 LLM 선택",
        options=["ollama", "gemini"],
        format_func=lambda x: "Ollama (로컬)" if x == "ollama" else "Gemini API",
        index=0,
        key="llm_backend",
    )

    llm_config = LLMConfig(backend=backend)

    if backend == "ollama":
        llm_config.ollama_model = st.sidebar.text_input(
            "Ollama 모델명",
            value="gemma3:4b",
            key="ollama_model",
        )
        llm_config.ollama_base_url = st.sidebar.text_input(
            "Ollama 서버 주소",
            value="http://localhost:11434",
            key="ollama_url",
        )
    else:
        llm_config.gemini_api_key = st.sidebar.text_input(
            "Gemini API 키",
            type="password",
            key="gemini_key",
        )
        llm_config.gemini_model = st.sidebar.selectbox(
            "Gemini 모델",
            options=["gemini-2.0-flash", "gemini-2.5-flash", "gemini-2.5-pro"],
            key="gemini_model",
        )

    llm_config.temperature = st.sidebar.slider(
        "Temperature",
        min_value=0.0,
        max_value=1.5,
        value=0.8,
        step=0.1,
        key="temperature",
    )

    st.sidebar.divider()

    st.sidebar.subheader("시뮬레이션 환경")

    sim_config = SimulationConfig()

    col1, col2 = st.sidebar.columns(2)
    with col1:
        sim_config.time_start = st.text_input(
            "시작 시간",
            value="08:00",
            key="time_start",
        )
    with col2:
        sim_config.time_end = st.text_input(
            "종료 시간",
            value="22:00",
            key="time_end",
        )

    sim_config.time_step_hours = st.sidebar.selectbox(
        "시간 간격 (시간)",
        options=[1, 2, 3, 4],
        index=1,
        key="time_step",
    )

    sim_config.total_days = st.sidebar.number_input(
        "시뮬레이션 일수",
        min_value=1,
        max_value=7,
        value=2,
        key="total_days",
    )

    sim_config.turns_per_round = st.sidebar.number_input(
        "라운드당 발언 횟수",
        min_value=2,
        max_value=10,
        value=4,
        key="turns_per_round",
    )

    locations_text = st.sidebar.text_area(
        "장소 목록 (줄바꿈으로 구분)",
        value="집\n학교\n카페\n레스토랑\n도서관\n공원\n편의점",
        height=150,
        key="locations",
    )
    sim_config.locations = [
        loc.strip() for loc in locations_text.strip().split("\n") if loc.strip()
    ]

    return llm_config, sim_config
