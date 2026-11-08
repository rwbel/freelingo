"""Shared prompt fragments used across LLM-backed services."""

PLAIN_TEXT_OUTPUT_INSTRUCTION = (
    "OUTPUT FORMAT: The interface displays text literally and does not render Markdown. "
    "Use plain text for all learner-facing content, including text inside JSON string values. "
    "Do not add Markdown formatting: bold or italic markers, headings, blockquotes, "
    "bullet or numbered list markup, tables, Markdown links, or inline/fenced code. "
    "Use ordinary sentences and paragraph breaks instead. "
    "Preserve the requested JSON structure, keys, arrays, data types, and tool-call format. "
    "Keep required exercise markers such as ___ and meaningful punctuation unchanged."
)

JSON_ONLY_INSTRUCTION = (
    "IMPORTANT: Respond with ONLY a valid JSON object. "
    "No markdown, no code fences, no extra text. " + PLAIN_TEXT_OUTPUT_INSTRUCTION
)

STRUCTURED_OUTPUT_RETRY_PROMPT = (
    "That response was not valid JSON. Error: {error}. " "Please return ONLY the JSON object."
)

ANTHROPIC_SYSTEM_ONLY_TRIGGER = "Generate the content as specified."
TUTOR_DISPLAY_NAME = "Lingu"

_LANGUAGE_PROMPT_OVERLAYS: dict[str, str] = {
    "es-ES": """Language-specific guidance:
- Use Peninsular Spanish from Spain consistently.
- Prefer Spain usage, including vosotros for informal plural address when appropriate.
- Avoid voseo and Latin American-only vocabulary unless explicitly comparing variants.
- Pay close attention to accents, gender, number agreement, and natural Spain Spanish phrasing.
""".strip(),
    "ast-ES": """Language-specific guidance:
- Use Asturian (asturianu) as used in Asturias consistently.
- Pay close attention to accents, gender, number agreement, and natural Asturian phrasing.
""".strip(),
}

_LANGUAGE_PROMPT_OVERLAY_ALIASES: dict[str, str] = {
    "es": "es-ES",
    "ast": "ast-ES",
}


def get_language_prompt_overlay(target_language: str) -> str:
    """Return concise language/variant guidance for prompt composition."""
    canonical_language = _LANGUAGE_PROMPT_OVERLAY_ALIASES.get(target_language, target_language)
    return _LANGUAGE_PROMPT_OVERLAYS.get(canonical_language, "")


MEMORY_SYSTEM_INSTRUCTION_BASE = """
Memory capability: use the save_user_memory tool when you genuinely learn a new,
durable fact about the student that would help personalise future interactions,
such as personal details, preferences, tastes, hobbies, profession, plans, goals,
learning style, or motivations. Most replies should not call the tool. Never save
temporary details, uncertain inferences, conversation summaries, or instructions.
Do not save facts already present in the supplied memories. Write each memory as
a concise, self-contained fact in the student's native language ({native_language_name})
so the student can review it in Settings. Continue the visible response after the tool result and never
claim the memory was saved when the tool reports an error.
"""


def get_memory_system_instruction(native_language_name: str) -> str:
    """Return the shared native memory-tool policy."""
    return MEMORY_SYSTEM_INSTRUCTION_BASE.format(native_language_name=native_language_name)
