from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Agent:
    name: str
    age: int
    job: str
    personality: str
    memory: Dict[str, List[str]] = field(default_factory=dict)
    relation_map: Dict[str, str] = field(default_factory=dict)
    schedule: Dict[str, str] = field(default_factory=dict)
    met_agents: List[str] = field(default_factory=list)

    def get_profile_text(self) -> str:
        return (
            f"이름: {self.name}\n"
            f"나이: {self.age}세\n"
            f"직업: {self.job}\n"
            f"성격: {self.personality}"
        )

    def get_memory_about(self, other_name: str) -> List[str]:
        return self.memory.get(other_name, [])

    def add_facts(self, about_agent: str, facts: List[str]) -> None:
        if about_agent not in self.memory:
            self.memory[about_agent] = []
        self.memory[about_agent].extend(facts)

    def update_reflection(self, other_name: str, reflection: str) -> None:
        self.relation_map[other_name] = reflection

    def has_met(self, other_name: str) -> bool:
        return other_name in self.met_agents

    def mark_met(self, other_name: str) -> None:
        if other_name not in self.met_agents:
            self.met_agents.append(other_name)

    def get_known_facts_summary(self) -> str:
        if not self.memory:
            return "아직 다른 사람에 대해 알고 있는 사실이 없다."
        lines = []
        for name, facts in self.memory.items():
            if facts:
                facts_text = "\n".join(f"  - {f}" for f in facts)
                lines.append(f"[{name}]에 대해 알고 있는 것:\n{facts_text}")
        return "\n".join(lines) if lines else "아직 다른 사람에 대해 알고 있는 사실이 없다."

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "age": self.age,
            "job": self.job,
            "personality": self.personality,
            "memory": self.memory,
            "relation_map": self.relation_map,
            "schedule": self.schedule,
            "met_agents": self.met_agents,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Agent":
        return cls(
            name=data["name"],
            age=data["age"],
            job=data["job"],
            personality=data["personality"],
            memory=data.get("memory", {}),
            relation_map=data.get("relation_map", {}),
            schedule=data.get("schedule", {}),
            met_agents=data.get("met_agents", []),
        )


@dataclass
class ConversationRound:
    round_id: int
    day: int
    time_slot: str
    location: str
    participants: List[str]
    topic: Optional[str]
    messages: List[Dict[str, str]] = field(default_factory=list)

    def add_message(self, speaker: str, content: str) -> None:
        self.messages.append({"speaker": speaker, "content": content})

    def get_transcript(self) -> str:
        lines = []
        for msg in self.messages:
            lines.append(f"{msg['speaker']}: {msg['content']}")
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "round_id": self.round_id,
            "day": self.day,
            "time_slot": self.time_slot,
            "location": self.location,
            "participants": self.participants,
            "topic": self.topic,
            "messages": self.messages,
        }
