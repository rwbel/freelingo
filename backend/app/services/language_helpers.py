"""Helpers for BCP-47 target_language codes.

Used by service layer to translate the generic target_language field into
human-readable names, self-names, ISO 639-1 codes, and flag emojis.
"""

from __future__ import annotations

from datetime import UTC, datetime

_LANGUAGE_INFO: dict[str, dict[str, str]] = {
    "es-ES": {
        "name": "Spanish (Spain)",
        "self_name": "Español (España)",
        "iso639": "es",
        "flag": "🇪🇸",
    },
    "ast-ES": {
        "name": "Asturian (Spain)",
        "self_name": "Asturianu (Asturies)",
        "iso639": "ast",
        "flag": "🇪🇸",
    },
}

_LANGUAGE_CAPABILITIES: dict[str, dict[str, str | bool]] = {
    "es-ES": {
        "script": "latin",
        "romanization": "",
        "uses_word_spacing": True,
        "reading_length_unit": "words",
    },
    "ast-ES": {
        "script": "latin",
        "romanization": "",
        "uses_word_spacing": True,
        "reading_length_unit": "words",
    },
}

_LANGUAGE_CAPABILITY_ALIASES: dict[str, str] = {
    "es": "es-ES",
    "ast": "ast-ES",
}

_VOICE_SESSION_TITLES: dict[str, str] = {
    "es": "Sesión de voz",
    "ast": "Sesión de voz",
}

_NATIVE_LANGUAGE_NAMES: dict[str, str] = {
    "es": "Spanish",
    "ast": "Asturian",
}

_LESSON_PRACTICE_TITLES: dict[str, str] = {
    "es": "Práctica",
    "ast": "Práctica",
}

_MONTH_NAMES: dict[str, list[str]] = {
    "es": [
        "enero",
        "febrero",
        "marzo",
        "abril",
        "mayo",
        "junio",
        "julio",
        "agosto",
        "septiembre",
        "octubre",
        "noviembre",
        "diciembre",
    ],
    "ast": [
        "xineru",
        "febreru",
        "marzu",
        "abril",
        "mayu",
        "xunu",
        "xunetu",
        "agostu",
        "setiembre",
        "ochobre",
        "payares",
        "avientu",
    ],
}


def voice_session_title(native_language: str) -> str:
    """Return a localized voice-session title with current date.

    Falls back to Spanish if the native language is not supported.
    """
    label = _VOICE_SESSION_TITLES.get(native_language, "Sesión de voz")
    now = datetime.now(UTC).replace(tzinfo=None)
    months = _MONTH_NAMES.get(native_language)
    if months:
        month_name = months[now.month - 1]
        if native_language in ("es", "ast"):
            return f"{label} — {now.day} de {month_name} de {now.year}"
        return f"{label} — {now.day} {month_name} {now.year}"
    return f"{label} — {now.strftime('%B %d, %Y')}"


def lesson_practice_title(native_language: str, lesson_title: str) -> str:
    label = _LESSON_PRACTICE_TITLES.get(native_language, "Práctica")
    return f"{label}: {lesson_title}"[:200]


def get_language_info(code: str) -> dict[str, str]:
    """Return display info for a target_language code.

    Falls back to the base ISO-639 code if the full BCP-47 tag is unknown.
    """
    if code in _LANGUAGE_INFO:
        return _LANGUAGE_INFO[code]
    base = code.split("-")[0]
    if base in _LANGUAGE_CAPABILITY_ALIASES:
        return _LANGUAGE_INFO[_LANGUAGE_CAPABILITY_ALIASES[base]]
    return {"name": code, "self_name": code, "iso639": base, "flag": "🏳️"}


def get_language_capability(code: str) -> dict[str, str | bool]:
    """Return rendering capability flags for a target_language code."""
    if code in _LANGUAGE_CAPABILITIES:
        return _LANGUAGE_CAPABILITIES[code]
    base = code.split("-")[0]
    if base in _LANGUAGE_CAPABILITY_ALIASES:
        return _LANGUAGE_CAPABILITIES[_LANGUAGE_CAPABILITY_ALIASES[base]]
    return {
        "script": "latin",
        "romanization": "",
        "uses_word_spacing": True,
        "reading_length_unit": "words",
    }


def get_native_language_name(code: str) -> str:
    """Return the English name of a native language code."""
    return _NATIVE_LANGUAGE_NAMES.get(code, code)

def get_language_name(code: str) -> str:
    """Return the English display name of a target language code (e.g., 'Spanish (Spain)')."""
    return get_language_info(code)["name"]

def get_iso639(code: str) -> str:
    """Extract ISO 639-1 code from a BCP-47 language tag (e.g., 'es-ES' -> 'es')."""
    return code.split("-")[0]

def get_comprehension_length_guidance(code: str, word_count: int) -> str:
    """Return comprehension length guidance for a target language."""
    cap = get_language_capability(code)
    if cap["reading_length_unit"] == "words":
        return f"{word_count} words"
    # For character-based languages (Chinese, Japanese, Korean)
    return f"{word_count * 2}–{word_count * 3} characters"

def get_language_flag(code: str) -> str:
    """Return flag emoji for a target language code."""
    return get_language_info(code)["flag"]


def get_language_self_name(code: str) -> str:
    """Return the self-name (native name) for a target language code."""
    return get_language_info(code)["self_name"]


def get_language_script(code: str) -> str:
    """Return the script type for a target language code."""
    return get_language_capability(code)["script"]


def get_language_romanization(code: str) -> str:
    """Return the romanization type for a target language code."""
    return get_language_capability(code)["romanization"]


def get_reading_length_unit(code: str) -> str:
    """Return the reading length unit for a target language code."""
    return get_language_capability(code)["reading_length_unit"]


def uses_word_spacing(code: str) -> bool:
    """Return whether the target language uses word spacing."""
    return get_language_capability(code)["uses_word_spacing"]
