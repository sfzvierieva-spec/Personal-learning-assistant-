"""Thin wrapper around the LLM APIs (Claude or Gemini).

Everything else in the module only sees one function type:

    llm(system: str, messages: list[dict]) -> str

so tests can pass a fake function instead of calling the real API, and the
provider can be swapped without touching the generator.

Config (environment variables, e.g. in a local ``.env`` — never committed):
- ``LLM_PROVIDER``        ``claude`` (default) or ``gemini``
- ``STUDY_AGENT_MODEL``   optional, overrides the default model of the provider

Claude:
- ``ANTHROPIC_API_KEY``
- ``ANTHROPIC_WORKSPACE_ID`` only if the API key is not tied to a workspace

Gemini (has a free tier, key from aistudio.google.com):
- ``GEMINI_API_KEY``
"""

from __future__ import annotations

import os
import time
from typing import Callable

import anthropic

LLMFunction = Callable[[str, list[dict]], str]

DEFAULT_MODELS = {"claude": "claude-opus-5", "gemini": "gemini-flash-latest"}
MAX_OUTPUT_TOKENS = 32000
RATE_LIMIT_RETRIES = 3        # the Gemini free tier has a low requests-per-minute limit
RATE_LIMIT_WAIT_SECONDS = 20

try:  # optional: load a local .env if python-dotenv is installed
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


class LLMError(Exception):
    """Raised when the API call fails or the answer cannot be used."""


def provider() -> str:
    name = os.getenv("LLM_PROVIDER", "claude").strip().lower()
    if name not in DEFAULT_MODELS:
        raise LLMError(f"Unknown LLM_PROVIDER '{name}' (use 'claude' or 'gemini').")
    return name


def model_name() -> str:
    return os.getenv("STUDY_AGENT_MODEL") or DEFAULT_MODELS[provider()]


def call_llm(system: str, messages: list[dict]) -> str:
    """Default LLM function: send the request to the configured provider."""
    return _call_gemini(system, messages) if provider() == "gemini" else _call_claude(system, messages)


# --------------------------------------------------------------------------- #
# Claude (Anthropic).
# --------------------------------------------------------------------------- #
_claude_client: anthropic.Anthropic | None = None


def _get_claude_client() -> anthropic.Anthropic:
    global _claude_client
    if _claude_client is None:
        workspace = os.getenv("ANTHROPIC_WORKSPACE_ID")
        headers = {"anthropic-workspace-id": workspace} if workspace else None
        _claude_client = anthropic.Anthropic(default_headers=headers)
    return _claude_client


def _call_claude(system: str, messages: list[dict]) -> str:
    """Streaming is used because answers can be long (a full quiz or summary) and
    a non-streamed request may hit the HTTP timeout. ``fallbacks="default"``
    lets the API retry on another model if the request is refused.
    """
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise LLMError("ANTHROPIC_API_KEY is not set (put it in a .env file at the project root).")

    try:
        with _get_claude_client().beta.messages.stream(
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


# --------------------------------------------------------------------------- #
# Gemini (Google).
# --------------------------------------------------------------------------- #
_gemini_client = None


def _call_gemini(system: str, messages: list[dict]) -> str:
    # Imported here so the Claude-only setup does not need the google package.
    from google import genai
    from google.genai import errors, types

    global _gemini_client
    if not os.getenv("GEMINI_API_KEY"):
        raise LLMError("GEMINI_API_KEY is not set (put it in a .env file at the project root).")
    if _gemini_client is None:
        _gemini_client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

    # Gemini calls the assistant role "model".
    contents = [
        types.Content(role="model" if m["role"] == "assistant" else "user",
                      parts=[types.Part(text=m["content"])])
        for m in messages
    ]
    config = types.GenerateContentConfig(system_instruction=system,
                                         max_output_tokens=MAX_OUTPUT_TOKENS,
                                         automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True))

    for attempt in range(RATE_LIMIT_RETRIES + 1):
        try:
            response = _gemini_client.models.generate_content(
                model=model_name(), contents=contents, config=config)
            break
        except errors.ClientError as exc:
            if exc.code == 429 and attempt < RATE_LIMIT_RETRIES:
                time.sleep(RATE_LIMIT_WAIT_SECONDS * (attempt + 1))
                continue
            if exc.code == 429:
                raise LLMError("Gemini free-tier limit reached, try again later.") from exc
            raise LLMError(f"Gemini error {exc.code}: {exc.message}") from exc
        except errors.ServerError as exc:  # 503 "high demand" is frequent on the free tier
            if attempt < RATE_LIMIT_RETRIES:
                time.sleep(RATE_LIMIT_WAIT_SECONDS * (attempt + 1))
                continue
            raise LLMError(f"Gemini is overloaded ({exc.code}), try again later.") from exc
        except errors.APIError as exc:
            raise LLMError(f"Gemini error {exc.code}: {exc.message}") from exc

    finish = response.candidates[0].finish_reason if response.candidates else None
    if finish == types.FinishReason.MAX_TOKENS:
        raise LLMError("The answer was too long and got cut. Ask for fewer items.")
    if not response.text:
        raise LLMError(f"Gemini returned no text (finish reason: {finish}).")
    return response.text
