from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Callable

from models.agent import Agent, ConversationRound
from services.llm_client import BaseLLMClient
from services.conversation import run_conversation_round
from services.memory import extract_and_store_facts, update_reflections
from services.planning import generate_daily_plan
from services.report import save_report_to_file
from config import SimulationConfig

logger = logging.getLogger(__name__)


@dataclass
class SimulationState:
    agents: Dict[str, Agent] = field(default_factory=dict)
    conversations: List[ConversationRound] = field(default_factory=list)
    current_day: int = 1
    current_time_slot: str = ""
    round_counter: int = 0
    is_running: bool = False
    is_finished: bool = False
    log: List[str] = field(default_factory=list)

    def add_log(self, message: str) -> None:
        self.log.append(message)
        logger.info(message)


def group_agents_by_location(
    agents: Dict[str, Agent],
    time_slot: str,
) -> Dict[str, List[Agent]]:
    location_groups: Dict[str, List[Agent]] = {}
    for agent in agents.values():
        location = agent.schedule.get(time_slot, "집")
        if location not in location_groups:
            location_groups[location] = []
        location_groups[location].append(agent)
    return location_groups


def run_simulation_step(
    llm: BaseLLMClient,
    state: SimulationState,
    config: SimulationConfig,
    time_slot: str,
    day: int,
    on_progress: Optional[Callable[[str], None]] = None,
) -> List[ConversationRound]:
    rounds = []

    location_groups = group_agents_by_location(state.agents, time_slot)

    for location, group in location_groups.items():
        if len(group) < 2:
            if on_progress:
                on_progress(
                    f"[{day}일차 {time_slot}] {location}: {group[0].name if group else '없음'} (혼자 있음)"
                )
            continue

        participant_names = [a.name for a in group]
        if on_progress:
            on_progress(
                f"[{day}일차 {time_slot}] {location}: {', '.join(participant_names)} 대화 시작"
            )

        state.round_counter += 1
        conv = run_conversation_round(
            llm=llm,
            participants=group,
            turns=config.turns_per_round,
            round_id=state.round_counter,
            day=day,
            time_slot=time_slot,
            location=location,
        )

        state.conversations.append(conv)
        rounds.append(conv)

        if on_progress:
            on_progress(f"  대화 완료 ({len(conv.messages)}건의 발언)")
            on_progress(f"  Fact 추출 중...")

        extracted = extract_and_store_facts(llm, conv, state.agents)
        total_facts = sum(len(f) for f in extracted.values())

        if on_progress:
            on_progress(f"  Fact {total_facts}건 추출 완료")
            on_progress(f"  Reflection 업데이트 중...")

        update_reflections(llm, conv, state.agents)

        if on_progress:
            on_progress(f"  Reflection 업데이트 완료")

    return rounds


def run_full_simulation(
    llm: BaseLLMClient,
    state: SimulationState,
    config: SimulationConfig,
    on_progress: Optional[Callable[[str], None]] = None,
) -> None:
    state.is_running = True
    time_slots = config.get_time_slots()

    for day in range(1, config.total_days + 1):
        state.current_day = day
        msg = f"=== {day}일차 시작 ==="
        state.add_log(msg)
        if on_progress:
            on_progress(msg)

        if on_progress:
            on_progress(f"각 Agent의 일정을 수립합니다...")

        for agent in state.agents.values():
            agent.schedule = generate_daily_plan(
                llm, agent, config.locations, time_slots, day
            )
            schedule_text = ", ".join(
                f"{t}:{l}" for t, l in sorted(agent.schedule.items())
            )
            log_msg = f"  {agent.name}의 일정: {schedule_text}"
            state.add_log(log_msg)
            if on_progress:
                on_progress(log_msg)

        for time_slot in time_slots:
            state.current_time_slot = time_slot
            run_simulation_step(llm, state, config, time_slot, day, on_progress)

        state.add_log(f"=== {day}일차 종료 ===")
        if on_progress:
            on_progress(f"=== {day}일차 종료 ===")

    state.is_running = False
    state.is_finished = True
    if on_progress:
        on_progress("시뮬레이션이 완료되었습니다.")
