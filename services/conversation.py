from __future__ import annotations

import logging
from typing import List, Optional

from models.agent import Agent, ConversationRound
from services.llm_client import BaseLLMClient

logger = logging.getLogger(__name__)


def _build_system_prompt(agent: Agent, participants: List[Agent], is_first_meeting: bool) -> str:
    other_names = [p.name for p in participants if p.name != agent.name]
    others_text = ", ".join(other_names)

    prompt = (
        f"너는 '{agent.name}'이라는 사람이야. 아래는 너의 프로필이야:\n"
        f"{agent.get_profile_text()}\n\n"
        f"지금 {others_text}와 대화하고 있어.\n"
    )

    if is_first_meeting:
        prompt += (
            "상대방을 처음 만나는 상황이야. "
            "자연스럽게 인사하고 자기소개를 하면서 대화를 시작해. "
            "억지로 주제를 꺼내지 말고, 자연스러운 흐름을 따라가.\n"
        )

    memory_text = agent.get_known_facts_summary()
    if memory_text and "아직" not in memory_text:
        prompt += f"\n너가 현재 알고 있는 정보:\n{memory_text}\n"

    for other in other_names:
        if other in agent.relation_map:
            prompt += f"\n{other}와의 관계: {agent.relation_map[other]}\n"

    prompt += (
        "\n규칙:\n"
        "- 자연스럽고 일상적인 한국어 구어체로 말해.\n"
        "- 한두 문장 정도로 짧게 대답해. 너무 길게 말하지 마.\n"
        "- 상대방의 말에 반응하면서 대화를 이어가.\n"
        "- 너의 캐릭터 성격에 맞게 행동해.\n"
        "- 절대 '나는 AI' 같은 메타 발언을 하지 마.\n"
    )
    return prompt


def _build_topic_prompt(agent: Agent, participants: List[Agent]) -> str:
    other_names = [p.name for p in participants if p.name != agent.name]
    memory_text = agent.get_known_facts_summary()

    prompt = (
        f"너는 '{agent.name}'이야.\n"
        f"지금 {', '.join(other_names)}와 대화를 시작하려고 해.\n"
    )
    if memory_text and "아직" not in memory_text:
        prompt += f"너가 알고 있는 정보:\n{memory_text}\n"

    prompt += (
        "이 정보를 바탕으로, 자연스럽게 꺼낼 수 있는 대화 주제 하나를 짧게 제안해줘. "
        "주제만 한 줄로 답해줘."
    )
    return prompt


def generate_topic(
    llm: BaseLLMClient,
    agent: Agent,
    participants: List[Agent],
) -> str:
    messages = [
        {"role": "user", "content": _build_topic_prompt(agent, participants)}
    ]
    topic = llm.chat(messages, temperature=0.9)
    return topic.strip()


def run_conversation_round(
    llm: BaseLLMClient,
    participants: List[Agent],
    turns: int,
    round_id: int,
    day: int,
    time_slot: str,
    location: str,
    topic: Optional[str] = None,
) -> ConversationRound:
    first_meeting_pairs = set()
    for i, a in enumerate(participants):
        for j, b in enumerate(participants):
            if i < j and not a.has_met(b.name):
                first_meeting_pairs.add((a.name, b.name))

    has_any_first_meeting = len(first_meeting_pairs) > 0

    if topic is None and not has_any_first_meeting:
        topic = generate_topic(llm, participants[0], participants)

    conv = ConversationRound(
        round_id=round_id,
        day=day,
        time_slot=time_slot,
        location=location,
        participants=[p.name for p in participants],
        topic=topic,
    )

    agent_histories = {}
    for agent in participants:
        is_first = any(
            agent.name in pair for pair in first_meeting_pairs
        )
        system_prompt = _build_system_prompt(agent, participants, is_first)
        if topic:
            system_prompt += f"\n현재 대화 주제: {topic}\n"
        system_prompt += f"\n장소: {location}, 시간: {time_slot}\n"
        agent_histories[agent.name] = [{"role": "system", "content": system_prompt}]

    for turn_idx in range(turns):
        speaker = participants[turn_idx % len(participants)]

        history = agent_histories[speaker.name]

        response = llm.chat(history, temperature=0.8)
        response = response.strip()

        conv.add_message(speaker.name, response)

        for agent in participants:
            if agent.name == speaker.name:
                agent_histories[agent.name].append(
                    {"role": "assistant", "content": response}
                )
            else:
                agent_histories[agent.name].append(
                    {"role": "user", "content": f"{speaker.name}: {response}"}
                )

    for i, a in enumerate(participants):
        for j, b in enumerate(participants):
            if i < j:
                a.mark_met(b.name)
                b.mark_met(a.name)

    return conv
