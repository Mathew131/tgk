# api.py
from __future__ import annotations

import os
import requests

from dotenv import load_dotenv
load_dotenv()


DEFAULT_API_URL = os.getenv("LITELLM_API_URL", "https://litellm.tokengate.ru/v1/chat/completions")
DEFAULT_MODEL = os.getenv("LLM_MODEL", "openai/gpt-oss-20b")


def llm_generate_from_text(
    text: str,
    *,
    api_url: str = DEFAULT_API_URL,
    api_key: str | None = None,
    model: str = DEFAULT_MODEL,
    # system_prompt: str = "Ты редактор. Пиши по-русски, кратко и структурно. Не стесняйся разбивать на абзацы. Не пиши вначале фразу 'Пост‑выжимка'.",
    system_prompt = """
    Ты русский редактор. Пиши как можно лаконичней, только основную суть.

    ФОРМАТ ВЫВОДА (строго):
    - Первая строка: заголовок статьи (БЕЗ двоеточия, обрамлена *)
    - Далее пустая строка
    - Далее 2–4 абзаца текста. Каждый не более 40 слов.

    НЕ ДОБАВЛЯЙ никаких вводных слов, включая:
    "Пост-выжимка", "Кратко", "Резюме", "Вывод".
    """,

    user_prompt_template: str = (
        "Вот текст статьи. Сформулируй короткий пост-выжимку в районе 10-20 предложений. \n\n"
        "ТЕКСТ:\n{text}"
    ),
    timeout: int = 30,
) -> str:
    api_key = api_key or os.getenv("LITELLM_API_KEY")
    if not api_key:
        raise RuntimeError("Не задан LITELLM_API_KEY (переменная окружения)")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt_template.format(text=text)},
        ],
    }

    r = requests.post(api_url, headers=headers, json=payload, timeout=timeout)
    r.raise_for_status()

    data = r.json()
    return data["choices"][0]["message"]["content"]
