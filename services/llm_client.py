from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Optional

from config import LLMConfig

logger = logging.getLogger(__name__)


class BaseLLMClient(ABC):
    @abstractmethod
    def chat(self, messages: List[Dict[str, str]], temperature: float = 0.8) -> str:
        ...

    @abstractmethod
    def is_available(self) -> bool:
        ...


class OllamaClient(BaseLLMClient):
    def __init__(self, model: str, base_url: str, max_tokens: int = 1024):
        self.model = model
        self.base_url = base_url
        self.max_tokens = max_tokens

    def chat(self, messages: List[Dict[str, str]], temperature: float = 0.8) -> str:
        import ollama

        client = ollama.Client(host=self.base_url)
        response = client.chat(
            model=self.model,
            messages=messages,
            options={
                "temperature": temperature,
                "num_predict": self.max_tokens,
            },
        )
        return response["message"]["content"]

    def is_available(self) -> bool:
        try:
            import ollama

            client = ollama.Client(host=self.base_url)
            client.list()
            return True
        except Exception:
            return False


class GeminiClient(BaseLLMClient):
    def __init__(self, api_key: str, model: str, max_tokens: int = 1024):
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self._client = None

    def _get_client(self):
        if self._client is None:
            import google.generativeai as genai

            genai.configure(api_key=self.api_key)
            self._client = genai.GenerativeModel(self.model)
        return self._client

    def chat(self, messages: List[Dict[str, str]], temperature: float = 0.8) -> str:
        import google.generativeai as genai

        model = self._get_client()

        history = []
        last_content = ""
        for msg in messages:
            role = msg["role"]
            if role == "system":
                last_content = msg["content"] + "\n\n"
                continue
            if role == "assistant":
                role = "model"
            content = last_content + msg["content"]
            last_content = ""
            history.append({"role": role, "parts": [content]})

        if history:
            last_msg = history.pop()
            chat = model.start_chat(history=history)
            response = chat.send_message(
                last_msg["parts"][0],
                generation_config=genai.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=self.max_tokens,
                ),
            )
            return response.text
        return ""

    def is_available(self) -> bool:
        if not self.api_key:
            return False
        try:
            self._get_client()
            return True
        except Exception:
            return False


def create_llm_client(config: LLMConfig) -> BaseLLMClient:
    if config.backend == "gemini":
        return GeminiClient(
            api_key=config.gemini_api_key,
            model=config.gemini_model,
            max_tokens=config.max_tokens,
        )
    else:
        return OllamaClient(
            model=config.ollama_model,
            base_url=config.ollama_base_url,
            max_tokens=config.max_tokens,
        )
