from __future__ import annotations

import logging
import random
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, time
from typing import Any

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reading import ReadingAttempt, ReadingExercise
from app.schemas.reading import ReadingGenerationResponse
from app.services.language_helpers import (
    get_comprehension_length_guidance,
    get_language_name,
)
from app.services.llm_adapter import LLMResponseError, llm_adapter
from app.services.progress_rewards import award_progress_reward
from app.services.progress_service import lock_progress_plan, update_daily_progress
from app.services.prompts.common import get_language_prompt_overlay
from app.services.prompts.comprehension import build_reading_generation_prompt

logger = logging.getLogger(__name__)

XP_PER_CORRECT_ANSWER = 10

# Valid exercise types per CEFR level
_TYPES_BY_LEVEL: dict[str, list[str]] = {
    "A1": ["notice", "email"],
    "A2": ["notice", "email"],
    "B1": ["email", "article", "news"],
    "B2": ["article", "news", "blog_post", "review"],
    "C1": ["news", "blog_post", "review", "essay"],
    "C2": ["review", "essay"],
}

_WORD_COUNT_BY_LEVEL: dict[str, int] = {
    "A1": 80,
    "A2": 120,
    "B1": 200,
    "B2": 280,
    "C1": 380,
    "C2": 480,
}

_TYPE_DESCRIPTIONS: dict[str, str] = {
    "notice": "a short public notice, sign, or instruction",
    "email": "a short informal or formal email message",
    "article": "a short informational or educational article",
    "news": "a news report on a current or recent event",
    "blog_post": "an informal blog-style opinion or personal piece",
    "review": "a review of a book, film, restaurant, or product",
    "essay": "a formal argumentative or discursive essay",
}

_TOPICS_BY_LEVEL: dict[str, list[str]] = {
    "A1": ["daily_routine", "family", "shopping", "home", "animals"],
    "A2": ["travel", "food", "weather", "hobbies", "school"],
    "B1": ["health", "work", "environment", "sports", "friendship"],
    "B2": ["technology", "culture", "education", "media", "money"],
    "C1": ["politics", "science", "literature", "psychology", "urban_life"],
    "C2": ["philosophy", "history", "global_affairs", "ethics", "economics"],
}

_CULTURAL_TOPICS: dict[str, list[str]] = {
    "es-ES": [
        "Spanish festivals and local traditions",
        "Spanish art, architecture, and flamenco",
        "daily life and customs in Spanish cities",
        "culture and diversity of Spanish-speaking countries",
    ],
    "ast-ES": [
        "Asturian festivals and local traditions",
        "Asturian literature, music, and cultural heritage",
        "daily life and customs in Asturian towns",
        "culture and diversity of Asturias",
    ],
    "es": [
        "Spanish festivals and local traditions",
        "Spanish art, architecture, and flamenco",
        "daily life and customs in Spanish cities",
        "culture and diversity of Spanish-speaking countries",
    ],
    "ast": [
        "Asturian festivals and local traditions",
        "Asturian literature, music, and cultural heritage",
        "daily life and customs in Asturian towns",
        "culture and diversity of Asturias",
    ],
}


def _get_cultural_topics(target_language: str) -> list[str]:
    topics = _CULTURAL_TOPICS.get(target_language)
    if topics is not None:
        return topics
    iso = target_language.split("-")[0].lower()
    return _CULTURAL_TOPICS.get(iso, _CULTURAL_TOPICS.get("es-ES", []))


async def get_available_exercise(
    level: str,
    target_language: str,
    user_id: int,
    db: AsyncSession,
) -> ReadingExercise | None:
    """Return an uncompleted exercise for this user at the given level, or None."""
    completed_subq = (
        select(ReadingAttempt.exercise_id)
        .where(ReadingAttempt.user_id == user_id)
        .scalar_subquery()
    )
    result = await db.execute(
        select(ReadingExercise)
        .where(
            ReadingExercise.level == level,
            ReadingExercise.target_language == target_language,
            ReadingExercise.id.not_in(completed_subq),
        )
        .order_by(ReadingExercise.created_at.asc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def generate_and_save_exercise(
    level: str,
    target_language: str,
    db: AsyncSession,
    *,
    deadline: float | None = None,
    before_save: Callable[[], Awaitable[None]] | None = None,
) -> ReadingExercise:
    if target_language not in _WORD_COUNT_BY_LEVEL:
        target_language = "es-ES"
    word_count = _WORD_COUNT_BY_LEVEL.get(level, 200)

    type_pool = _TYPES_BY_LEVEL.get(level, ["notice", "email"])
    exercise_type = random.choice(type_pool)
    topic_pool = _TOPICS_BY_LEVEL.get(level, ["daily_routine"])
    topic = random.choice(topic_pool)

    cultural_topics = _get_cultural_topics(target_language)
    cultural_context = random.choice(cultural_topics) if cultural_topics else ""

    prompt = build_reading_generation_prompt(
        exercise_type=exercise_type,
        level=level,
        target_language=target_language,
        topic=topic,
        word_count=word_count,
        cultural_context=cultural_context,
        language_prompt_overlay=get_language_prompt_overlay(target_language),
    )

    response = await llm_adapter.structured_output(
        [{"role": "system", "content": prompt}],
        ReadingGenerationResponse,
        timeout=60.0,
        max_retries=2,
    )

    exercise = ReadingExercise(
        level=level,
        target_language=target_language,
        exercise_type=exercise_type,
        topic=topic,
        passage=response.passage,
        questions=[q.model_dump() for q in response.questions],
        word_count=word_count,
    )

    if before_save:
        await before_save()

    db.add(exercise)
    await db.commit()
    await db.refresh(exercise)
    return exercise


async def grade_exercise(
    exercise_id: int,
    answers: list[str],
    db: AsyncSession,
) -> tuple[bool, list[bool], int]:
    exercise = await db.get(ReadingExercise, exercise_id)
    if exercise is None:
        raise ValueError("Exercise not found")

    correct_count = 0
    results = []
    questions = exercise.questions

    for i, (question, answer) in enumerate(zip(questions, answers)):
        expected = question.get("answer", "").strip().lower()
        given = answer.strip().lower()
        is_correct = expected == given
        results.append(is_correct)
        if is_correct:
            correct_count += 1

    passed = correct_count >= len(questions) * 0.6
    return passed, results, correct_count


async def process_exercise_attempt(
    user_id: int,
    exercise_id: int,
    answers: list[str],
    db: AsyncSession,
) -> dict[str, Any]:
    passed, results, correct_count = await grade_exercise(exercise_id, answers, db)

    xp_earned = correct_count * XP_PER_CORRECT_ANSWER
    if passed:
        xp_earned += 10

    attempt = ReadingAttempt(
        user_id=user_id,
        exercise_id=exercise_id,
        answers=answers,
        passed=passed,
        xp_earned=xp_earned,
    )
    db.add(attempt)

    await update_daily_progress(user_id, xp_earned, db)
    await award_progress_reward(user_id, xp_earned, db)
    await lock_progress_plan(user_id, db)

    await db.commit()

    return {
        "passed": passed,
        "results": results,
        "correct_count": correct_count,
        "total_questions": len(answers),
        "xp_earned": xp_earned,
    }


async def get_user_history(
    user_id: int,
    db: AsyncSession,
    skip: int = 0,
    limit: int = 10,
    target_language: str | None = None,
):
    stmt = (
        select(ReadingAttempt, ReadingExercise)
        .join(ReadingExercise, ReadingAttempt.exercise_id == ReadingExercise.id)
        .where(ReadingAttempt.user_id == user_id)
        .order_by(desc(ReadingAttempt.completed_at))
        .offset(skip)
        .limit(limit)
    )

    if target_language:
        stmt = stmt.where(ReadingExercise.target_language == target_language)

    result = await db.execute(stmt)
    rows = result.all()

    total_stmt = (
        select(ReadingAttempt.id)
        .join(ReadingExercise, ReadingAttempt.exercise_id == ReadingExercise.id)
        .where(ReadingAttempt.user_id == user_id)
    )
    if target_language:
        total_stmt = total_stmt.where(ReadingExercise.target_language == target_language)
    total_result = await db.execute(total_stmt)
    total = len(total_result.all())

    return rows, total


async def submit_attempt(
    user_id: int,
    exercise_id: int,
    answers: list[str],
    db: AsyncSession,
) -> dict[str, Any]:
    return await process_exercise_attempt(user_id, exercise_id, answers, db)
