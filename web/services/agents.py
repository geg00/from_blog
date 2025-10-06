"""Agent utilities combining search and LLM responses."""

from __future__ import annotations

from typing import List, Tuple

import requests
from bs4 import BeautifulSoup

from web.services.llm import call_openai


def search_duckduckgo(query: str, max_results: int = 3) -> List[str]:
    url = "https://html.duckduckgo.com/html/"
    params = {"q": query}
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; FastHTML-Agent/1.0)",
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=5)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        results: List[str] = []
        for result in soup.select("div.result"):
            title_elem = result.select_one("a.result__a")
            snippet_elem = result.select_one("a.result__snippet")
            if not title_elem:
                continue
            title = title_elem.get_text(strip=True)
            snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
            results.append(f"{title}\n{snippet}".strip())
            if len(results) >= max_results:
                break
        return results
    except Exception:  # pragma: no cover - network dependent
        return []


def process_agent_message(message: str) -> Tuple[str, str]:
    search_results = search_duckduckgo(message)
    if search_results:
        source = "search"
        context = "\n\n".join(search_results)
        prompt = (
            f"Search results:\n{context}\n\n"
            f"Question: {message}\n\n"
            "Use the search findings when relevant; otherwise answer from your knowledge."
        )
    else:
        source = "direct"
        prompt = message

    reply = call_openai(
        [
            {"role": "system", "content": "You are a helpful AI research assistant."},
            {"role": "user", "content": prompt},
        ]
    )
    return reply, source

__all__ = ["search_duckduckgo", "process_agent_message"]
