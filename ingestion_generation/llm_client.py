"""Thin wrapper around the Anthropic API (Claude).

Everything else in the module only sees one function type:

    llm(system: str, messages: list[dict]) -> str

so tests can pass a fake function instead of calling the real API, and the
provider could be swapped without touching the generator.

Config (environment variables, e.g. in a local ``.env`` — never committed):
- ``ANTHROPIC_API_KEY``   required for real calls
- ``STUDY_AGENT_MODEL``   optional, defaults to ``claude-opus-5``
"""

from __future__ import annotations

import os
from typing import Callable

import anthropic

LLMFunction = Callable[[str, list[dict]], str]

DEFAULT_MODEL = "claude-opus-5"
MAX_OUTPUT_TOKENS = 32000

try:  # optional: load a local .env if python-dotenv is installed
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


class LLMError(Exception):
    """Raised when the API call fails or the answer cannot be used."""


def model_name() -> str:
    return os.getenv("STUDY_AGENT_MODEL", DEFAULT_MODEL)


_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    return _client


def call_claude(system: str, messages: list[dict]) -> str:
    """Send one request to Claude and return the text of the answer.

    Streaming is used because answers can be long (a full quiz or summary) and
    a non-streamed request may hit the HTTP timeout. ``fallbacks="default"``
    lets the API retry on another model if the request is refused.
    """
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise LLMError("ANTHROPIC_API_KEY is not set (put it in a .env file at the project root).")

    try:
        with _get_client().beta.messages.stream(
            model=model_name(),
            max_tokens=MAX_OUTPUT_TOKENS,
            system=system,
            messages=messages,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        ) as stream:
            response = stream.get_final_message()
    except anthropic.AuthenticationError as exc:
        raise LLMError("Invalid or missing ANTHROPIC_API_KEY.") from exc
    except anthropic.RateLimitError as exc:
        raise LLMError("Rate limit reached, try again in a minute.") from exc
    except anthropic.APIStatusError as exc:
        raise LLMError(f"API error {exc.status_code}: {exc.message}") from exc
    except anthropic.APIConnectionError as exc:
        raise LLMError("Could not reach the API (network problem).") from exc

    if response.stop_reason == "refusal":
        raise LLMError("The model refused to process this content.")
    if response.stop_reason == "max_tokens":
        # The JSON would be cut in the middle: better to fail clearly.
        raise LLMError("The answer was too long and got cut. Ask for fewer items.")

    return "".join(block.text for block in response.content if block.type == "text")
