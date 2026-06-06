from __future__ import annotations

import json
import logging
from typing import List, Dict

from models.agent import Agent
from services.llm_client import BaseLLMClient

logger = logging.getLogger(__name__)


def generate_daily_plan(
    llm: BaseLLMClient,
    agent: Agent,
    locations: List[str],
    time_slots: List[str],
    day: int,
) -> Dict[str, str]:
    locations_text = ", ".join(locations)
    slots_text = ", ".join(time_slots)

    prompt = (
        f"너는 '{agent.name}'이야.\n"
        f"프로필:\n{agent.get_profile_text()}\n\n"
        f"오늘은 시뮬레이션 {day}일차야.\n"
        f"활동 가능한 장소: {locations_text}\n"
        f"시간대: {slots_text}\n\n"
    )

    memory_text = agent.get_known_facts_summary()
    if memory_text and "아직" not in memory_text:
        prompt += f"너가 알고 있는 사람들에 대한 정보:\n{memory_text}\n\n"

    prompt += (
        f"위 정보를 바탕으로, {agent.name}의 직업과 성격에 맞는 하루 일정을 짜줘.\n"
        f"반드시 아래 JSON 형식으로만 답해줘. 다른 텍스트 없이 JSON만 출력해:\n"
        f'{{"08:00": "장소", "10:00": "장소", ...}}\n'
        f"장소는 반드시 다음 중에서만 선택해: {locations_text}\n"
    )

    messages = [{"role": "user", "content": prompt}]
    response = llm.chat(messages, temperature=0.7)

    schedule = _parse_schedule(response, locations, time_slots)
    return schedule


def _parse_schedule(
    response: str,
    locations: List[str],
    time_slots: List[str],
) -> Dict[str, str]:
    text = response.strip()

    if "```" in text:
        parts = text.split("```")
        for part in parts:
            part = part.strip()
            if part.startswith("json"):
                part = part[4:].strip()
            if part.startswith("{"):
                text = part
                break

    start = text.find("{")
    end = text.rfind("}") + 1
    if start >= 0 and end > start:
        text = text[start:end]

    try:
        schedule = json.loads(text)
        valid_schedule = {}
        for slot in time_slots:
            if slot in schedule and schedule[slot] in locations:
                valid_schedule[slot] = schedule[slot]
            else:
                valid_schedule[slot] = locations[0]
        return valid_schedule
    except (json.JSONDecodeError, TypeError):
        return _default_schedule(locations, time_slots)


def _default_schedule(locations: List[str], time_slots: List[str]) -> Dict[str, str]:
    schedule = {}
    for i, slot in enumerate(time_slots):
        if i == 0 or i >= len(time_slots) - 1:
            schedule[slot] = locations[0]
        elif i < len(time_slots) // 2:
            schedule[slot] = locations[1] if len(locations) > 1 else locations[0]
        else:
            schedule[slot] = locations[2] if len(locations) > 2 else locations[0]
    return schedule
