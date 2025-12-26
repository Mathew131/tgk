# main.py
from __future__ import annotations

import asyncio
import os
import time
from pathlib import Path

from aiogram import Bot

from parse import parse_once_and_save, OUTPUT_FILE
from api import llm_generate_from_text


GENERATED_FILE = Path("generated_post.txt")

BOT_TOKEN = os.getenv("BOT_TOKEN")          # <- вместо хардкода
CHANNEL_ID = os.getenv("CHANNEL_ID")        # например: -1002942125256

async def send_to_telegram(text: str) -> None:
    if not BOT_TOKEN or not CHANNEL_ID:
        return  # просто молча пропускаем, если не настроено

    bot = Bot(token=BOT_TOKEN)
    await bot.send_message(chat_id=int(CHANNEL_ID), text=text, parse_mode="Markdown")


def run_once() -> None:
    article = parse_once_and_save()
    if article is None:
        print("Новых постов нет")
        return

    raw = OUTPUT_FILE.read_text(encoding="utf-8")
    result = llm_generate_from_text(raw)
    final_text = (
        f"{result}\n\n"
        f"{article.url}"
    )

    GENERATED_FILE.write_text(result, encoding="utf-8")
    print("Сгенерировала текст и сохранила в generated_post.txt")

    asyncio.run(send_to_telegram(final_text))
    print("Если TG настроен — отправила в канал")


def run_forever(period_seconds: int = 3600) -> None:
    while True:
        try:
            run_once()
        except Exception as e:
            print("Ошибка:", e)
        time.sleep(period_seconds)


if __name__ == "__main__":
    run_forever(3600)
