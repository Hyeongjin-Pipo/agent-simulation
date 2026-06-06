import os
from dataclasses import dataclass, field
from typing import List


@dataclass
class LLMConfig:
    backend: str = "ollama"
    ollama_model: str = "gemma3:4b"
    ollama_base_url: str = "http://localhost:11434"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    temperature: float = 0.8
    max_tokens: int = 1024


@dataclass
class SimulationConfig:
    time_start: str = "08:00"
    time_end: str = "22:00"
    time_step_hours: int = 2
    total_days: int = 2
    turns_per_round: int = 4
    locations: List[str] = field(default_factory=lambda: [
        "집",
        "학교",
        "카페",
        "레스토랑",
        "도서관",
        "공원",
        "편의점",
    ])

    def get_time_slots(self) -> List[str]:
        slots = []
        start_h = int(self.time_start.split(":")[0])
        end_h = int(self.time_end.split(":")[0])
        h = start_h
        while h <= end_h:
            slots.append(f"{h:02d}:00")
            h += self.time_step_hours
        return slots


DEFAULT_AGENTS = [
    {
        "name": "김민수",
        "age": 25,
        "job": "컴퓨터공학과 대학생",
        "personality": "활발하고 호기심이 많다. 새로운 사람 만나는 걸 좋아하고, 이야기를 잘 들어주는 편이다.",
        "initial_memory": {},
    },
    {
        "name": "이서연",
        "age": 28,
        "job": "동네 카페 사장",
        "personality": "따뜻하고 배려심이 깊다. 손님들 이름을 다 외울 정도로 사람에 관심이 많다.",
        "initial_memory": {},
    },
    {
        "name": "박준호",
        "age": 32,
        "job": "백엔드 개발자",
        "personality": "내성적이지만 유머감각이 있다. 관심사가 맞는 사람과는 몇 시간이고 이야기한다.",
        "initial_memory": {},
    },
    {
        "name": "최유나",
        "age": 22,
        "job": "음악대학 작곡과 학생",
        "personality": "밝고 긍정적이다. 감수성이 풍부하고, 사소한 일상도 재밌게 이야기한다.",
        "initial_memory": {},
    },
]
