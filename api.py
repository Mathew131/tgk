# api.py
from __future__ import annotations

import os
import requests

DEFAULT_API_URL = os.getenv("LITELLM_API_URL", "https://litellm.tokengate.ru/v1/chat/completions")
DEFAULT_MODEL = os.getenv("LLM_MODEL", "openai/gpt-oss-20b")


def llm_generate(text: str) -> str:
    api_key = os.getenv("LITELLM_API_KEY")
    if not api_key:
        raise RuntimeError("Не задан LITELLM_API_KEY (переменная окружения)")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    system_prompt = (
        "Ты редактор. Пиши по-русски, кратко и структурно. "
        "Начинай сразу с заголовка (без вводных фраз). "
        "Делай 2–5 абзацев и 3 буллета."
    )

    data = {
        "model": DEFAULT_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Текст статьи:\n\n{text}"},
        ],
    }

    r = requests.post(DEFAULT_API_URL, headers=headers, json=data, timeout=60)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]
