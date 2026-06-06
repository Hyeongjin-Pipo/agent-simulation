# 다중 에이전트 소셜 시뮬레이션

가상의 공간과 시간 위에서 여러 Agent가 자율적으로 대화하고, 서로에 대한 기억(Memory)과 관계(Reflection)를 형성해 나가는 웹 기반 시뮬레이션이다. Streamlit을 활용하여 대화 과정과 결과를 직관적으로 확인할 수 있도록 구현되었다.

## 실행 방법

Python 3.12 환경을 권장합니다.

```bash
pip install -r requirements.txt
streamlit run app.py
```

명령어 실행 한 후에 브라우저에서 `http://localhost:8501`로 접속하여 UI를 확인하시면 됩니다.

* LLM 백엔드는 사이드바에서 Ollama(로컬)와 Gemini API 중 선택하실 수 있습니다.
* Ollama를 사용할 경우 백그라운드에 `ollama serve`가 실행 중이어야 합니다.

## 프로젝트 구성

| 파일/폴더 | 역할 |
|---|---|
| `app.py` | Streamlit 메인 애플리케이션입니다. (3개의 탭으로 구성) |
| `config.py` | LLM, 시뮬레이션 환경(시간, 장소) 설정 및 프리셋 파일입니다. |
| `models/agent.py` | Agent 기본 정보, Memory, Relation Map 데이터 모델입니다. |
| `services/llm_client.py` | Ollama / Gemini API 연동 래퍼 모듈입니다. |
| `services/conversation.py`| 턴 기반 대화 및 주제를 생성하는 시스템입니다. |
| `services/memory.py` | 대화에서 Fact를 추출하고 Reflection을 업데이트하는 모듈입니다. |
| `services/planning.py` | Agent별로 시간대별 장소 계획(Daily Plan)을 수립합니다. |
| `services/report.py` | Markdown 형식으로 특정 Agent 시점의 리포트를 생성하고 저장합니다. |
| `simulation/engine.py` | 시간 순서대로 시뮬레이션을 진행하고, 같은 장소 내 Agent 간의 자동 대화를 매칭하는 엔진입니다. |
| `ui/` | 사이드바, Agent 관리, 시뮬레이션, 리포트 패널 등 화면을 구성하는 UI 컴포넌트 폴더입니다. |
| `reports/` | 최종 생성된 리포트 파일(.md)이 저장되는 경로입니다. |

## 요구사항 구현 내역

* **Agent 프로필 및 Memory:** 이름/나이/직업/성격 프로필과 상대방에 대한 사실을 기록하는 Memory를 구현했습니다.
* **초기 상태 주입:** UI를 통해 새로운 Agent 생성 시 초기 Memory를 주입하실 수 있습니다.
* **Relation Map (Reflection):** 대화 후 축적된 Memory를 바탕으로 각 Agent 쌍 간의 관계를 요약하여 갱신합니다.
* **대화 시스템:** 2명 이상의 Agent가 같은 장소에서 만나면 자연스러운 턴 기반 대화를 진행합니다. 처음 만날 때는 인사와 자기소개부터 시작합니다.
* **Fact 추출:** 대화 종료 후 LLM을 통해 상대방에 대한 구체적인 사실(Fact)만 추출하여 메모리에 저장합니다.
* **시뮬레이션 엔진:** 2일간(기본 08:00~22:00) 시간대별로 시뮬레이션이 진행됩니다. 매일 아침 Agent가 스스로 일정을 계획하고, 같은 장소에 있는 사람과 대화가 발생하도록 구현했습니다.
* **결과 리포트:** 2일간의 시뮬레이션 종료 후 특정 Agent 시점의 결과를 마크다운(.md) 파일로 출력하고 다운로드 받으실 수 있도록 했습니다.
