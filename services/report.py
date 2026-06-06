from __future__ import annotations

import os
from datetime import datetime
from typing import Dict

from models.agent import Agent


def generate_report_text(agent: Agent, all_agents: Dict[str, Agent]) -> str:
    lines = []
    lines.append(f"{agent.name}의 시뮬레이션 리포트")
    lines.append(f"작성 시점: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("")
    lines.append(f"프로필")
    lines.append(f"이름: {agent.name}")
    lines.append(f"나이: {agent.age}세")
    lines.append(f"직업: {agent.job}")
    lines.append(f"성격: {agent.personality}")
    lines.append("")
    lines.append("-" * 50)
    lines.append("")

    other_agents = [
        name for name in agent.met_agents
        if name in all_agents and name != agent.name
    ]

    if not other_agents:
        lines.append("아직 만난 사람이 없다.")
        return "\n".join(lines)

    for other_name in other_agents:
        lines.append(f"[{other_name}]에 대하여")
        lines.append("")

        facts = agent.get_memory_about(other_name)
        lines.append("알고 있는 사실:")
        if facts:
            for idx, fact in enumerate(facts, 1):
                lines.append(f"  {idx}. {fact}")
        else:
            lines.append("  (아직 알고 있는 사실이 없음)")
        lines.append("")

        reflection = agent.relation_map.get(other_name, "")
        lines.append("관계 및 인상:")
        if reflection:
            lines.append(f"  {reflection}")
        else:
            lines.append("  (아직 관계에 대한 정리가 없음)")
        lines.append("")
        lines.append("-" * 50)
        lines.append("")

    return "\n".join(lines)


def save_report_to_file(
    agent: Agent,
    all_agents: Dict[str, Agent],
    output_dir: str = "reports",
) -> str:
    os.makedirs(output_dir, exist_ok=True)

    report_text = generate_report_text(agent, all_agents)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"report_{agent.name}_{timestamp}.md"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(report_text)

    return filepath
