"""Register Minion as a Hermes web search provider."""

from .provider import MinionWebSearchProvider


def register(ctx) -> None:
    ctx.register_web_search_provider(MinionWebSearchProvider())
