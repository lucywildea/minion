"""Hermes web search provider backed by the local Minion binary."""

from __future__ import annotations

import os
import shutil
import subprocess
from typing import Any, Dict, Iterable
from urllib.parse import urlsplit

import yaml

from agent.web_search_provider import WebSearchProvider  # type: ignore[import-not-found]

_SEARCH_TIMEOUT_SECONDS = 180
_DESCRIPTION_LIMIT = 1200
_PASSTHROUGH_ENV = (
    "HOME",
    "PATH",
    "USER",
    "LOGNAME",
    "TMPDIR",
    "TEMP",
    "TMP",
    "LANG",
    "LC_ALL",
    "XDG_CONFIG_HOME",
    "XDG_CACHE_HOME",
    "SYSTEMROOT",
    "WINDIR",
    "COMSPEC",
    "PATHEXT",
)


def _subprocess_environment() -> dict[str, str]:
    """Return only environment values Minion needs to find user configuration."""
    return {key: os.environ[key] for key in _PASSTHROUGH_ENV if key in os.environ}


def _documents(stream: str) -> Iterable[dict[str, Any]]:
    for document in yaml.safe_load_all(stream):
        if isinstance(document, dict):
            yield document


def _compact(value: Any, limit: int = _DESCRIPTION_LIMIT) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def _title(record: dict[str, Any], url: str) -> str:
    title = _compact(record.get("title"), 240)
    if title:
        return title
    return urlsplit(url).netloc or url


def _normalize(stream: str, limit: int) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    seen: set[str] = set()
    for record in _documents(stream):
        url = str(record.get("url") or "").strip()
        if not url or url in seen:
            continue
        seen.add(url)
        description = _compact(record.get("summary") or record.get("text"))
        results.append(
            {
                "title": _title(record, url),
                "url": url,
                "description": description,
                "position": len(results) + 1,
            }
        )
        if len(results) >= limit:
            break
    return results


class MinionWebSearchProvider(WebSearchProvider):
    """Run Minion inline searches and normalize its FileRecord YAML stream."""

    @property
    def name(self) -> str:
        return "minion"

    @property
    def display_name(self) -> str:
        return "Minion"

    def is_available(self) -> bool:
        return shutil.which("minion") is not None

    def supports_search(self) -> bool:
        return True

    def supports_extract(self) -> bool:
        return False

    def search(self, query: str, limit: int = 5) -> Dict[str, Any]:
        query = str(query or "").strip()
        if not query:
            return {"success": False, "error": "Minion search requires a query"}

        binary = shutil.which("minion")
        if binary is None:
            return {
                "success": False,
                "error": "Minion is not installed or is not available on PATH",
            }

        safe_limit = max(1, int(limit))
        command = [
            binary,
            "run",
            f"from.search={query}",
            f"from.limit={safe_limit}",
        ]

        try:
            completed = subprocess.run(
                command,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=_subprocess_environment(),
                timeout=_SEARCH_TIMEOUT_SECONDS,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"Minion search timed out after {_SEARCH_TIMEOUT_SECONDS} seconds",
            }
        except OSError:
            return {"success": False, "error": "Minion search could not be started"}

        try:
            results = _normalize(completed.stdout, safe_limit)
        except yaml.YAMLError:
            return {"success": False, "error": "Minion returned invalid YAML"}

        if results:
            return {"success": True, "data": {"web": results}}

        if completed.returncode != 0:
            return {
                "success": False,
                "error": f"Minion search failed with exit code {completed.returncode}",
            }

        return {"success": True, "data": {"web": []}}
