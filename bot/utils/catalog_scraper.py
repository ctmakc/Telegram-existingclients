from __future__ import annotations

import asyncio
import html
import re
from urllib.request import Request, urlopen

USER_AGENT = "Mozilla/5.0 (compatible; MiniMeltsCatalogBot/1.0)"


def _clean_text(value: str) -> str:
    text = html.unescape(value)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_flavors_from_html(page_html: str) -> list[str]:
    # Primary source: footer columns usually contain a concise canonical flavor list.
    names: list[str] = []
    seen: set[str] = set()

    for block in re.findall(
        r'<ul[^>]*class="[^"]*footer_tastes_column[^"]*"[^>]*>(.*?)</ul>',
        page_html,
        flags=re.IGNORECASE | re.DOTALL,
    ):
        for raw in re.findall(r"<li[^>]*>(.*?)</li>", block, flags=re.IGNORECASE | re.DOTALL):
            name = _clean_text(raw)
            key = name.casefold()
            if not name or key in seen:
                continue
            seen.add(key)
            names.append(name)

    if len(names) >= 8:
        return names

    # Fallback: parse slug names from taste text images.
    slug_names = re.findall(
        r'/wp-content/uploads/[^"]*/([a-z0-9_]+)_text(?:-\d+)?\.webp',
        page_html,
        flags=re.IGNORECASE,
    )
    for slug in slug_names:
        name = slug.replace("_", " ").strip().title()
        key = name.casefold()
        if key in seen:
            continue
        seen.add(key)
        names.append(name)
    return names


def fetch_flavors(url: str, timeout: int = 20) -> list[str]:
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=timeout) as resp:  # nosec B310 - fixed HTTPS URL from config/admin
        page_html = resp.read().decode("utf-8", errors="ignore")
    return extract_flavors_from_html(page_html)


async def fetch_flavors_async(url: str, timeout: int = 20) -> list[str]:
    return await asyncio.to_thread(fetch_flavors, url, timeout)
