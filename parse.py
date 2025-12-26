# parse.py
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import requests
from bs4 import BeautifulSoup


FLOW_URL = "https://habr.com/ru/flows/ai_and_ml/articles/rated10/"
STATE_FILE = Path("state.json")
OUTPUT_FILE = Path("latest_post.txt")
DEBUG_HTML = Path("debug_last_article.html")

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.7,en;q=0.6",
    "Referer": "https://habr.com/",
    "Connection": "keep-alive",
})


@dataclass(frozen=True)
class Article:
    id: str
    title: str
    url: str
    text: str


def _load_state(state_file: Path = STATE_FILE) -> dict:
    if not state_file.exists():
        return {}
    try:
        txt = state_file.read_text(encoding="utf-8").strip()
        return json.loads(txt) if txt else {}
    except json.JSONDecodeError:
        return {}


def _save_state(state: dict, state_file: Path = STATE_FILE) -> None:
    state_file.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")


def _fetch_html(url: str, timeout: int = 20) -> str:
    r = SESSION.get(url, timeout=timeout)
    r.raise_for_status()
    return r.text


def _looks_like_block_page(soup: BeautifulSoup) -> bool:
    text = soup.get_text(" ", strip=True).lower()
    bad_markers = ["доступ ограничен", "captcha", "капча", "подтвердите", "robot", "cloudflare"]
    return any(m in text for m in bad_markers)


def _get_latest_article_meta_from_flow(flow_url: str = FLOW_URL) -> dict:
    html = _fetch_html(flow_url)
    soup = BeautifulSoup(html, "html.parser")

    item = soup.select_one("article.tm-articles-list__item")
    if item is None:
        raise RuntimeError("Не нашла ни одной статьи в ленте (разметка изменилась или блок).")

    link = item.select_one("a.tm-title__link")
    if link is None or not link.get("href"):
        raise RuntimeError("Не нашла ссылку на статью в первом элементе ленты.")

    href = link["href"]
    url = href if href.startswith("http") else ("https://habr.com" + href)
    title = link.get_text(strip=True)

    return {"id": href, "title": title, "url": url}


def _pick_article_container(soup: BeautifulSoup):
    selectors = [
        "[data-article-body]",
        "div.tm-article-body",
        "div.tm-article-presenter__content",
        "div.article-formatted-body",
        "article",  # fallback
    ]
    for sel in selectors:
        node = soup.select_one(sel)
        if node is not None:
            return node
    return None


def _extract_text_from_container(container) -> str:
    blocks: list[str] = []
    for tag in container.find_all(["h1", "h2", "h3", "p", "li", "pre", "blockquote", "figcaption"]):
        txt = tag.get_text("\n", strip=True)
        if txt:
            blocks.append(txt)
    return "\n\n".join(blocks).strip()


def _fetch_article_text(article_url: str) -> str:
    html = _fetch_html(article_url)
    soup = BeautifulSoup(html, "html.parser")

    if _looks_like_block_page(soup):
        DEBUG_HTML.write_text(html, encoding="utf-8")
        raise RuntimeError("Habr отдал страницу-ограничение (капча/блок). Сохранила debug_last_article.html")

    container = _pick_article_container(soup)
    if container is None:
        DEBUG_HTML.write_text(html, encoding="utf-8")
        raise RuntimeError("Не нашла контейнер статьи. Сохранила debug_last_article.html")

    text = _extract_text_from_container(container)
    if not text:
        DEBUG_HTML.write_text(html, encoding="utf-8")
        raise RuntimeError("Контейнер найден, но текст пустой. Сохранила debug_last_article.html")

    return text


def parse_once_and_save(
    flow_url: str = FLOW_URL,
    state_file: Path = STATE_FILE,
    output_file: Path = OUTPUT_FILE,
) -> Optional[Article]:
    """
    1) берёт самый свежий пост из ленты
    2) если он новый — качает полный текст
    3) перезаписывает output_file
    Возвращает Article, если пост новый, иначе None.
    """
    state = _load_state(state_file)
    last_id = state.get("last_id")

    meta = _get_latest_article_meta_from_flow(flow_url)
    if meta["id"] == last_id:
        return None

    text = _fetch_article_text(meta["url"])
    article = Article(id=meta["id"], title=meta["title"], url=meta["url"], text=text)

    output_file.write_text(f"{article.title}\n{article.url}\n\n{article.text}", encoding="utf-8")

    state["last_id"] = meta["id"]
    _save_state(state, state_file)

    return article
