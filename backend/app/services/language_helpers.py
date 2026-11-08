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
                                            }

_LANGUAGE_CAPABILITIES: dict[str, dict[str, str | bool]] = {
                            "es-ES": {
        "script": "latin",
        "romanization": "",
        "uses_word_spacing": True,
        "reading_length_unit": "words",
    },
                                }

_LANGUAGE_CAPABILITY_ALIASES: dict[str, str] = {
    "es": "es-ES",
}

_VOICE_SESSION_TITLES: dict[str, str] = {
    "es": "Sesión de voz",
    "fr": "Session vocale",
    "pt": "Sessão de voz",
    "de": "Sprachsitzung",
    "it": "Sessione vocale",
    "pl": "Sesja głosowa",
    "nl": "Spraaksessie",
    "ro": "Sesiune vocală",
    "ru": "Голосовая сессия",
    "tr": "Sesli oturum",
    "sv": "Röstsamtal",
    "da": "Stemmesamtale",
    "fi": "Äänikeskustelu",
    "hr": "Glasovni razgovor",
}

_NATIVE_LANGUAGE_NAMES: dict[str, str] = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "pt": "Portuguese",
    "de": "German",
    "it": "Italian",
    "pl": "Polish",
    "nl": "Dutch",
    "ro": "Romanian",
    "ru": "Russian",
    "tr": "Turkish",
    "sv": "Swedish",
    "da": "Danish",
    "fi": "Finnish",
    "hr": "Croatian",
}

_LESSON_PRACTICE_TITLES: dict[str, str] = {
    "en": "Practice",
    "es": "Práctica",
    "fr": "Pratique",
    "pt": "Prática",
    "de": "Übung",
    "it": "Pratica",
    "pl": "Ćwiczenie",
    "nl": "Oefening",
    "ro": "Practică",
    "ru": "Практика",
    "tr": "Pratik",
    "sv": "Övning",
    "da": "Øvelse",
    "fi": "Harjoitus",
    "hr": "Vježba",
}


def lesson_practice_title(native_language: str, lesson_title: str) -> str:
    label = _LESSON_PRACTICE_TITLES.get(native_language, "Practice")
    return f"{label}: {lesson_title}"[:200]


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
    "fr": [
        "janvier",
        "février",
        "mars",
        "avril",
        "mai",
        "juin",
        "juillet",
        "août",
        "septembre",
        "octobre",
        "novembre",
        "décembre",
    ],
    "pt": [
        "janeiro",
        "fevereiro",
        "março",
        "abril",
        "maio",
        "junho",
        "julho",
        "agosto",
        "setembro",
        "outubro",
        "novembro",
        "dezembro",
    ],
    "de": [
        "Januar",
        "Februar",
        "März",
        "April",
        "Mai",
        "Juni",
        "Juli",
        "August",
        "September",
        "Oktober",
        "November",
        "Dezember",
    ],
    "it": [
        "gennaio",
        "febbraio",
        "marzo",
        "aprile",
        "maggio",
        "giugno",
        "luglio",
        "agosto",
        "settembre",
        "ottobre",
        "novembre",
        "dicembre",
    ],
    "pl": [
        "stycznia",
        "lutego",
        "marca",
        "kwietnia",
        "maja",
        "czerwca",
        "lipca",
        "sierpnia",
        "września",
        "października",
        "listopada",
        "grudnia",
    ],
    "nl": [
        "januari",
        "februari",
        "maart",
        "april",
        "mei",
        "juni",
        "juli",
        "augustus",
        "september",
        "oktober",
        "november",
        "december",
    ],
    "ro": [
        "ianuarie",
        "februarie",
        "martie",
        "aprilie",
        "mai",
        "iunie",
        "iulie",
        "august",
        "septembrie",
        "octombrie",
        "noiembrie",
        "decembrie",
    ],
    "ru": [
        "января",
        "февраля",
        "марта",
        "апреля",
        "мая",
        "июня",
        "июля",
        "августа",
        "сентября",
        "октября",
        "ноября",
        "декабря",
    ],
    "tr": [
        "Ocak",
        "Şubat",
        "Mart",
        "Nisan",
        "Mayıs",
        "Haziran",
        "Temmuz",
        "Ağustos",
        "Eylül",
        "Ekim",
        "Kasım",
        "Aralık",
    ],
    "sv": [
        "januari",
        "februari",
        "mars",
        "april",
        "maj",
        "juni",
        "juli",
        "augusti",
        "september",
        "oktober",
        "november",
        "december",
    ],
    "da": [
        "januar",
        "februar",
        "marts",
        "april",
        "maj",
        "juni",
        "juli",
        "august",
        "september",
        "oktober",
        "november",
        "december",
    ],
    "fi": [
        "tammikuuta",
        "helmikuuta",
        "maaliskuuta",
        "huhtikuuta",
        "toukokuuta",
        "kesäkuuta",
        "heinäkuuta",
        "elokuuta",
        "syyskuuta",
        "lokakuuta",
        "marraskuuta",
        "joulukuuta",
    ],
    "hr": [
        "siječnja",
        "veljače",
        "ožujka",
        "travnja",
        "svibnja",
        "lipnja",
        "srpnja",
        "kolovoza",
        "rujna",
        "listopada",
        "studenoga",
        "prosinca",
    ],
}


def get_language_name(target_language: str) -> str:
    """'es-ES' → 'Italian', 'es-ES' → 'English (US)'"""
    info = _LANGUAGE_INFO.get(target_language)
    return info["name"] if info else target_language


def get_language_self_name(target_language: str) -> str:
    """'es-ES' → 'Italiano', 'es-ES' → 'Español'"""
    info = _LANGUAGE_INFO.get(target_language)
    return info["self_name"] if info else target_language


def get_iso639(target_language: str) -> str:
    """'es-ES' → 'en', 'es-ES' → 'it'"""
    info = _LANGUAGE_INFO.get(target_language)
    return info["iso639"] if info else target_language.split("-")[0].lower()


def get_language_flag(target_language: str) -> str:
    """'es-ES' → '🇪🇸', 'es-ES' → '🇮🇹'"""
    info = _LANGUAGE_INFO.get(target_language)
    return info["flag"] if info else ""


def _get_language_capability(target_language: str) -> dict[str, str | bool]:
    canonical_language = _LANGUAGE_CAPABILITY_ALIASES.get(target_language, target_language)
    if canonical_language not in _LANGUAGE_CAPABILITIES:
        iso_language = target_language.split("-")[0].lower()
        canonical_language = _LANGUAGE_CAPABILITY_ALIASES.get(iso_language, canonical_language)
    return _LANGUAGE_CAPABILITIES.get(canonical_language, _LANGUAGE_CAPABILITIES["es-ES"])


def get_language_script(target_language: str) -> str:
    """Return the primary writing-system metadata for a target language."""
    return str(_get_language_capability(target_language)["script"])


def get_language_romanization(target_language: str) -> str:
    """Return the romanization system used as learner support, or an empty string."""
    return str(_get_language_capability(target_language)["romanization"])


def uses_word_spacing(target_language: str) -> bool:
    """Return whether ordinary text uses visible spaces between words."""
    return bool(_get_language_capability(target_language)["uses_word_spacing"])


def get_reading_length_unit(target_language: str) -> str:
    """Return the best length unit for generated reading/listening prompts."""
    return str(_get_language_capability(target_language)["reading_length_unit"])


def get_comprehension_length_guidance(target_language: str, base_word_count: int) -> str:
    """Return language-aware length guidance for generated comprehension content."""
    unit = get_reading_length_unit(target_language)
    if unit == "characters":
        return f"{base_word_count * 2}–{base_word_count * 3} characters"
    return f"{base_word_count} words"


def get_native_language_name(native_language: str) -> str:
    """Return a human-readable name for native language codes used by user profiles."""
    return _NATIVE_LANGUAGE_NAMES.get(native_language, native_language)


def voice_session_title(native_language: str) -> str:
    """Return a localized 'Voice session - date' title for a conversation.

    Falls back to English if the native language is not supported.
    """
    label = _VOICE_SESSION_TITLES.get(native_language, "Voice session")
    now = datetime.now(UTC).replace(tzinfo=None)
    months = _MONTH_NAMES.get(native_language)
    if months:
        month_name = months[now.month - 1]
        if native_language in ("es", "pt"):
            return f"{label} — {now.day} de {month_name} de {now.year}"
        if native_language in ("de", "da", "fi"):
            return f"{label} — {now.day}. {month_name} {now.year}"
        if native_language == "hr":
            return f"{label} — {now.day}. {month_name} {now.year}."
        return f"{label} — {now.day} {month_name} {now.year}"
    return f"{label} — {now.strftime('%B %d, %Y')}"
