"""Small, dependency-free helpers for the job-tracker Markdown contract."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from typing import Optional


_FRONTMATTER_FENCE = "---"
_WHITESPACE = re.compile(r"\s+")


def _normalize_text(value: str) -> str:
    """Normalize human-entered text without removing URL punctuation."""

    text = unicodedata.normalize("NFKC", "" if value is None else str(value))
    return _WHITESPACE.sub(" ", text).strip().casefold()


def _normalize_url(value: str) -> str:
    """Normalize a URL for identity while retaining its URL syntax."""

    return _normalize_text(value)


def parse_frontmatter(markdown: str) -> dict[str, object]:
    """Parse the simple YAML frontmatter supported by the toolkit.

    The contract intentionally supports scalar values, empty values, and
    JSON-compatible inline arrays. It does not attempt to be a general YAML
    parser, which keeps the public tooling dependency-free and predictable.
    """

    lines = markdown.splitlines()
    if lines and lines[0].startswith("\ufeff"):
        lines[0] = lines[0][1:]
    if not lines or lines[0].strip() != _FRONTMATTER_FENCE:
        raise ValueError("frontmatter must start with ---")

    fields: dict[str, object] = {}
    closing_index = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == _FRONTMATTER_FENCE:
            closing_index = index
            break

        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            raise ValueError(f"invalid frontmatter line {index + 1}: {line}")

        key, raw_value = line.split(":", 1)
        key = key.strip()
        if not key:
            raise ValueError(f"empty frontmatter key on line {index + 1}")
        if key in fields:
            raise ValueError(f"duplicate frontmatter key: {key}")
        fields[key] = _parse_value(raw_value.strip(), index + 1)

    if closing_index is None:
        raise ValueError("unterminated frontmatter")
    return fields


def _parse_value(raw_value: str, line_number: int) -> object:
    if not raw_value:
        return ""

    if raw_value.startswith("["):
        try:
            value = json.loads(raw_value)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"invalid inline JSON array on line {line_number}: {exc.msg}"
            ) from exc
        if not isinstance(value, list):
            raise ValueError(f"inline frontmatter value is not an array on line {line_number}")
        return value

    if raw_value.startswith('"'):
        try:
            value = json.loads(raw_value)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"invalid quoted value on line {line_number}: {exc.msg}"
            ) from exc
        if not isinstance(value, str):
            raise ValueError(f"quoted frontmatter value is not a string on line {line_number}")
        return value

    if raw_value.startswith("'") and raw_value.endswith("'") and len(raw_value) >= 2:
        return raw_value[1:-1].replace("''", "'")

    return raw_value


def normalize_component(value: str) -> str:
    """Return the first-release identity form for a text component."""

    text = unicodedata.normalize("NFKC", "" if value is None else str(value))
    text = "".join(character for character in text if not unicodedata.category(character).startswith("P"))
    text = text.casefold()
    return _WHITESPACE.sub(" ", text).strip()


def build_dedupe_key(
    company: str, department: str, position: str
) -> Optional[tuple[str, str, str]]:
    """Build the normalized company/department/position identity tuple."""

    key = (
        normalize_component(company),
        normalize_component(department),
        normalize_component(position),
    )
    return key if all(key) else None


def event_fingerprint(
    source: str,
    source_url: str,
    event_type: str,
    occurred_at: str,
    raw_status: str,
    dedupe_key: tuple[str, str, str],
) -> str:
    """Return a stable SHA-256 fingerprint for one observed event."""

    values = (
        _normalize_text(source),
        _normalize_url(source_url),
        _normalize_text(event_type),
        _normalize_text(occurred_at),
        _normalize_text(raw_status),
        *(normalize_component(component) for component in dedupe_key),
    )
    payload = "\x1f".join(values).encode("utf-8")
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"
