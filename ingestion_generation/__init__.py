"""Ingestion & Generation module: course upload, chunking, LLM calls, output formats.

Public API (what the interface imports):

- ``extract_text(source, filename=None) -> str``
- ``generate_content(course_text, system_prompt, output_format, user_context=None) -> dict``
- ``SUPPORTED_FORMATS``
"""

from .extraction import ExtractionError, extract_text
from .formats import SUPPORTED_FORMATS
from .generator import GenerationError, generate_content

__all__ = [
    "extract_text",
    "generate_content",
    "SUPPORTED_FORMATS",
    "ExtractionError",
    "GenerationError",
]
