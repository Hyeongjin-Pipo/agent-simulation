from __future__ import annotations

import json
import logging
from typing import List, Dict

from models.agent import Agent, ConversationRound
from services.llm_client import BaseLLMClient

logger = logging.getLogger(__name__)


def _parse_fact_list(raw_text: str) -> List[str]:
    facts = []
    for line in raw_text.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        for prefix in ["- ", "* ", "• "]:
            if line.startswith(prefix):
                line = line[len(prefix):]
                break
        if len(line) > 2 and line[0].isdigit() and line[1] in (".", ")"):
            line = line[2:].strip()
        elif len(line) > 3 and line[:2].isdigit() and line[2] in (".", ")"):
            line = line[3:].strip()
        if line:
            facts.append(line)
    return facts


def extract_facts_about_agent(
    llm: BaseLLMClient,
    conversation: ConversationRound,
    target_agent_name: str,
) -> List[str]:
    transcript = conversation.get_transcript()

    prompt = (
        f"아래는 여러 사람이 나눈 대화 내용이야.\n\n"
        f"--- 대화 내용 ---\n{transcript}\n--- 대화 끝 ---\n\n"
        f"이 대화에서 '{target_agent_name}'에 대해 알 수 있는 사실(Fact)을 추출해줘.\n"
        f"직접적으로 언급되었거나 대화를 통해 유추할 수 있는 구체적인 정보만 포함해.\n"
        f"추측이나 일반적인 내용은 제외해.\n"
        f"각 사실을 한 줄에 하나씩, 짧고 명확하게 적어줘.\n"
        f"사실이 없으면 '없음'이라고만 답해줘.\n"
    )

    messages = [{"role": "user", "content": prompt}]
    response = llm.chat(messages, temperature=0.3)

    if "없음" in response.strip() and len(response.strip()) < 10:
        return []

    return _parse_fact_list(response)


def extract_and_store_facts(
    llm: BaseLLMClient,
    conversation: ConversationRound,
    agents: Dict[str, Agent],
) -> Dict[str, List[str]]:
    all_facts = {}

    for target_name in conversation.participants:
        facts = extract_facts_about_agent(llm, conversation, target_name)
        all_facts[target_name] = facts

        if not facts:
            continue

        for other_name in conversation.participants:
            if other_name != target_name and other_name in agents:
                agents[other_name].add_facts(target_name, facts)

    return all_facts


def generate_reflection(
    llm: BaseLLMClient,
    agent: Agent,
    other_agent: Agent,
) -> str:
    facts = agent.get_memory_about(other_agent.name)
    existing_reflection = agent.relation_map.get(other_agent.name, "")

    prompt = (
        f"너는 '{agent.name}'의 입장에서 '{other_agent.name}'과의 관계를 정리하고 있어.\n\n"
    )

    if existing_reflection:
        prompt += f"기존에 {other_agent.name}에 대해 가지고 있던 인상:\n{existing_reflection}\n\n"

    if facts:
        facts_text = "\n".join(f"- {f}" for f in facts)
        prompt += f"{other_agent.name}에 대해 알고 있는 사실:\n{facts_text}\n\n"
    else:
        prompt += f"{other_agent.name}에 대해 아직 알고 있는 사실이 거의 없어.\n\n"

    prompt += (
        f"위 정보를 종합하여, {agent.name}의 입장에서 {other_agent.name}과의 관계를 "
        f"2~3문장으로 자연스럽게 요약해줘. "
        f"{agent.name}의 성격({agent.personality})이 반영되도록 써줘.\n"
        f"요약만 답해줘."
    )

    messages = [{"role": "user", "content": prompt}]
    reflection = llm.chat(messages, temperature=0.5)
    return reflection.strip()


def update_reflections(
    llm: BaseLLMClient,
    conversation: ConversationRound,
    agents: Dict[str, Agent],
) -> None:
    participant_names = conversation.participants

    for i, name_a in enumerate(participant_names):
        for j, name_b in enumerate(participant_names):
            if i >= j:
                continue
            agent_a = agents.get(name_a)
            agent_b = agents.get(name_b)
            if not agent_a or not agent_b:
                continue

            reflection_ab = generate_reflection(llm, agent_a, agent_b)
            agent_a.update_reflection(name_b, reflection_ab)

            reflection_ba = generate_reflection(llm, agent_b, agent_a)
            agent_b.update_reflection(name_a, reflection_ba)
