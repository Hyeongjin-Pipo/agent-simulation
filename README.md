# 다중 에이전트 소셜 시뮬레이션

가상의 공간과 시간 위에서 여러 Agent가 자율적으로 대화하고, 서로에 대한 기억(Memory)과 관계(Reflection)를 형성해 나가는 시뮬레이션이다.


## 실행 방법

```bash
pip install -r requirements.txt
streamlit run app.py
```

브라우저에서 `http://localhost:8501`로 접속한다.

LLM 백엔드는 사이드바에서 Ollama(로컬)와 Gemini API 중 선택할 수 있다.
Ollama를 사용할 경우 `ollama serve`가 실행 중이어야 한다.


## 프로젝트 구조

```
agent-simulation/
    app.py                    메인 Streamlit 앱
    config.py                 LLM, 시뮬레이션 환경 설정
    requirements.txt          의존성 목록
    models/
        agent.py              Agent 데이터 모델
    services/
        llm_client.py         LLM 클라이언트 (Ollama / Gemini)
        conversation.py       턴 기반 대화 시스템
        memory.py             Fact 추출, Memory 저장, Reflection 업데이트
        planning.py           시간대별 장소 계획 수립
        report.py             리포트 생성 및 파일 저장
    simulation/
        engine.py             시뮬레이션 엔진
    ui/
        sidebar.py            사이드바 설정 UI
        agent_panel.py        Agent 관리 UI
        simulation_panel.py   시뮬레이션 실행 UI
        report_panel.py       리포트 출력 UI
    reports/                  생성된 리포트 저장 폴더
```


## 구현 내역

### 기본 구조

- Agent는 이름, 나이, 직업, 성격 정보를 가진다.
- Agent는 Memory를 가진다. 대화에서 추출된 사실(Fact)을 상대방별로 누적 저장한다.
- Agent는 Relation Map을 가진다. 다른 Agent와의 관계 요약(Reflection)을 저장한다.
- Agent 생성 시 초기 Memory를 주입할 수 있다.

### 대화 시스템

- 2명 이상의 Agent가 한 라운드에서 대화할 수 있다.
- 라운드마다 참여 Agent와 발언 횟수(turns)를 개별 설정할 수 있다.
- 대화 주제는 선택 사항이다. 지정하지 않으면 Agent가 Memory를 기반으로 주제를 생성한다.
- 처음 만나는 Agent와는 인사와 자기소개부터 시작하며, 주제를 강제로 꺼내지 않는다.

### Fact 추출 및 Reflection

- 한 라운드의 대화가 끝나면 LLM이 각 Agent에 대한 사실(Fact)을 추출한다.
- 추출된 Fact는 해당 Agent를 제외한 나머지 참여자의 Memory에 저장된다.
- 한 라운드가 끝나면 참여한 모든 Agent 쌍에 대해 Reflection이 업데이트된다.

### 리포트

- 시뮬레이션 종료 후 특정 Agent 시점의 리포트를 출력한다.
- 리포트는 상대방별로 알고 있는 사실, 관계/Reflection 순으로 나열한다.
- 리포트를 .md 파일로 저장하거나 브라우저에서 다운로드할 수 있다.

### 추가 구현 과제

- 가상의 활동 시간 범위를 설정한다 (기본값 08:00 ~ 22:00).
- 가상의 공간 목록을 정의한다 (집, 학교, 카페, 레스토랑, 도서관, 공원, 편의점).
- 하루 시작 전 각 Agent가 Planning Prompt를 통해 시간대별 장소 계획을 수립한다.
- 시뮬레이션이 시간 순서로 진행되며, 같은 장소에 있는 Agent들끼리 자동으로 대화한다.
- 가상의 이틀이 지난 후 특정 한 Agent 기준의 리포트를 파일로 저장한다.


## 사용 기술

- Python 3.12
- Streamlit (웹 UI)
- Ollama (로컬 LLM 추론)
- Google Generative AI (Gemini API)
