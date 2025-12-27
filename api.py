# api.py
from __future__ import annotations

import os
import requests

DEFAULT_API_URL = os.getenv(
    "LITELLM_API_URL",
    "https://litellm.tokengate.ru/v1/chat/completions"
)
DEFAULT_MODEL = os.getenv("LLM_MODEL", "openai/gpt-oss-20b")


def llm_generate(text: str) -> str:
    api_key = os.getenv("LITELLM_API_KEY")
    if not api_key:
        raise RuntimeError("Не задан LITELLM_API_KEY (переменная окружения)")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    system_prompt = """
    Ты русский редактор, пишущий на русском языке. Пиши как можно лаконичней, только основную суть.

    ФОРМАТ ВЫВОДА (строго):
    - Первая строка: заголовок статьи (БЕЗ двоеточия, обрамлена *)
    - Далее пустая строка
    - Далее 2–4 абзаца текста. Каждый не более 40 слов.

    НЕ ДОБАВЛЯЙ вводных слов:
    "Пост-выжимка", "Кратко", "Резюме", "Вывод".
    """

    data = {
        "model": DEFAULT_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt.strip()},
            {"role": "user", "content": f"Текст статьи:\n\n{text}"},
        ],
    }

    r = requests.post(DEFAULT_API_URL, headers=headers, json=data, timeout=60)
    r.raise_for_status()

    generated = r.json()["choices"][0]["message"]["content"].strip()

    return f"{generated}"
