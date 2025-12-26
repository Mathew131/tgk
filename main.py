# main.py
from __future__ import annotations

import asyncio
import os
import time
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()  # важно ДО импортов, которые читают env

from aiogram import Bot

from parse import parse_once_for_flow, DATA_DIR
from api import llm_generate


FLOWS = [
    ("backend", "https://habr.com/ru/flows/backend/articles/", "CHANNEL_BACKEND"),
    ("admin", "https://habr.com/ru/flows/admin/articles/", "CHANNEL_ADMIN"),
    ("infosec", "https://habr.com/ru/flows/information_security/articles/", "CHANNEL_INFOSEC"),
    ("gamedev", "https://habr.com/ru/flows/gamedev/articles/", "CHANNEL_GAMEDEV"),
    ("ai_ml", "https://habr.com/ru/flows/ai_and_ml/articles/", "CHANNEL_AI_ML"),
    ("design", "https://habr.com/ru/flows/design/articles/", "CHANNEL_DESIGN"),
    # ("management", "https://habr.com/ru/flows/management/articles/", "CHANNEL_MANAGEMENT"),
    # ("marketing", "https://habr.com/ru/flows/marketing/articles/", "CHANNEL_MARKETING"),
    # ("popsci", "https://habr.com/ru/flows/popsci/articles/", "CHANNEL_POPSCI"),
    # ("all", "https://habr.com/ru/articles/", "CHANNEL_ALL"),
]

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("Не задан BOT_TOKEN в .env/окружении")


def channel_id_from_env(env_name: str) -> int | None:
    v = os.getenv(env_name)
    if not v:
        return None
    return int(v)


async def send_to_telegram(channel_id: int, text: str) -> None:
    bot = Bot(token=BOT_TOKEN)
    # Markdown как ты хотел: ссылка первой строкой + текст
    await bot.send_message(chat_id=channel_id, text=text, parse_mode="Markdown")
    await bot.session.close()


def run_once_all() -> None:
    for flow, url, channel_env in FLOWS:
        ch_id = channel_id_from_env(channel_env)
        if ch_id is None:
            print(f"[{flow}] пропуск: не задан {channel_env}")
            continue

        try:
            article = parse_once_for_flow(flow, url)
            if article is None:
                print(f"[{flow}] новых постов нет")
                continue

            # В нейронку отдаём весь latest_<flow>.txt (заголовок+ссылка+текст)
            latest_path = DATA_DIR / f"latest_{flow}.txt"
            raw = latest_path.read_text(encoding="utf-8")

            generated = generated = llm_generate(raw)

            out_path = DATA_DIR / f"generated_{flow}.txt"
            out_path.write_text(generated, encoding="utf-8")

            final_text = f"{generated}\n\n{article.url}"

            asyncio.run(send_to_telegram(ch_id, final_text))
            print(f"[{flow}] отправила в канал")

            time.sleep(2)  # маленькая пауза, чтобы не долбить Telegram/Habr

        except Exception as e:
            print(f"[{flow}] ошибка: {e}")


def run_forever(period_seconds: int = 3600) -> None:
    while True:
        run_once_all()
        time.sleep(period_seconds)


if __name__ == "__main__":
    run_forever(3600)
