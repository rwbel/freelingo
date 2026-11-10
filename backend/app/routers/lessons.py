from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_db
from app.models.lesson import Exercise
from app.models.user import User
from app.schemas.lessons import (
    ExerciseFeedbackRequest,
    ExerciseFeedbackResponse,
    ExerciseType,
    LessonExerciseResponse,
    LessonGenerateRequest,
    LessonGenerateResponse,
    LessonProgressResponse,
    LessonStartResponse,
    LessonSubmitRequest,
    LessonSubmitResponse,
    PronunciationExerciseRequest,
    PronunciationExerciseResponse,
)
from app.utils.lesson_exercises import normalized_exercise_text

router = APIRouter(prefix="/api/lessons", tags=["lessons"])


_ANSWER_FEEDBACK: dict[str, dict[str, str]] = {
    "es": {
        "correct": "Correcto!",
        "correct_answer": "La respuesta correcta es: {answer}",
        "free_write_unavailable": "No se pudo evaluar la respuesta escrita en este momento.",
        "good_pronunciation": "Buena pronunciación!",
        "target_phrase": "La frase objetivo era: {answer}",
    },
    "ast": {
        "correct": "Corretu!",
        "correct_answer": "La respuesta correuta ye: {answer}",
        "free_write_unavailable": "Nun se pudo evaluar la respuesta escrita nesti momentu.",
        "good_pronunciation": "Bona pronunciación!",
        "target_phrase": "La frase oxetivu yera: {answer}",
    },
}


def _answer_feedback(native_language: str, key: str, *, answer: str = "") -> str:
    messages = _ANSWER_FEEDBACK.get(native_language, _ANSWER_FEEDBACK["es"])
    return messages[key].format(answer=answer)


def _exercise_has_technical_error(exercise: Exercise) -> bool:
    if not exercise.question.strip() or not exercise.correct_answer.strip():
        return True
    if exercise.exercise_type in (
        ExerciseType.MULTIPLE_CHOICE,
        ExerciseType.TRANSLATION_CHOICE,
        ExerciseType.LISTENING_CHOICE,
    ):
        options = exercise.options or []
        if len(options) < 2 or exercise.correct_answer not in options:
            return True
    return False


@router.get("/{plan_id}/current", response_model=LessonStartResponse)
async def get_current_lesson(
    plan_id: int,
    user: User = Depends(lambda: None),  # placeholder
    db: AsyncSession = Depends(get_db),
):
    from app.models.study_plan import StudyPlan
    from app.models.lesson import Lesson

    plan = await db.get(StudyPlan, plan_id)
    if not plan or plan.user_id != user.id:
        raise HTTPException(status_code=404, detail="Study plan not found")

    lesson = (
        await db.execute(
            select(Lesson)
            .where(Lesson.study_plan_id == plan_id, Lesson.order == plan.current_unit)
            .limit(1)
        )
    ).scalar_one_or_none()

    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    exercises = [
        LessonExerciseResponse(
            id=ex.id,
            exercise_type=ex.exercise_type,
            question=ex.question,
            options=ex.options,
            correct_answer=ex.correct_answer,
            audio_url=ex.audio_url,
        )
        for ex in lesson.exercises
    ]

    return LessonStartResponse(
        lesson_id=lesson.id,
        title=lesson.title,
        exercises=exercises,
        xp_reward=lesson.xp_reward,
    )


@router.post("/generate", response_model=LessonGenerateResponse)
async def generate_lesson(
    payload: LessonGenerateRequest,
    user: User = Depends(lambda: None),  # placeholder
    db: AsyncSession = Depends(get_db),
):
    from app.services.lesson_generator import generate_lesson as gen_lesson
    from app.models.study_plan import StudyPlan

    plan = await db.get(StudyPlan, payload.study_plan_id)
    if not plan or plan.user_id != user.id:
        raise HTTPException(status_code=404, detail="Study plan not found")

    lesson = await gen_lesson(
        db=db,
        study_plan=plan,
        cefr_level=payload.cefr_level,
        target_language=plan.target_language,
        native_language=user.native_language,
        unit=payload.unit,
        topic=payload.topic,
    )

    return LessonGenerateResponse(lesson_id=lesson.id, title=lesson.title)


@router.post("/{lesson_id}/start", response_model=LessonStartResponse)
async def start_lesson(
    lesson_id: int,
    user: User = Depends(lambda: None),  # placeholder
    db: AsyncSession = Depends(get_db),
):
    from app.models.lesson import Lesson

    lesson = await db.get(Lesson, lesson_id)
    if not lesson or lesson.study_plan.user_id != user.id:
        raise HTTPException(status_code=404, detail="Lesson not found")

    exercises = [
        LessonExerciseResponse(
            id=ex.id,
            exercise_type=ex.exercise_type,
            question=ex.question,
            options=ex.options,
            correct_answer=ex.correct_answer,
            audio_url=ex.audio_url,
        )
        for ex in lesson.exercises
    ]

    return LessonStartResponse(
        lesson_id=lesson.id,
        title=lesson.title,
        exercises=exercises,
        xp_reward=lesson.xp_reward,
    )


@router.post("/{lesson_id}/exercise/feedback", response_model=ExerciseFeedbackResponse)
async def exercise_feedback(
    lesson_id: int,
    payload: ExerciseFeedbackRequest,
    user: User = Depends(lambda: None),  # placeholder
    db: AsyncSession = Depends(get_db),
):
    from app.models.lesson import Lesson

    lesson = await db.get(Lesson, lesson_id)
    if not lesson or lesson.study_plan.user_id != user.id:
        raise HTTPException(status_code=404, detail="Lesson not found")

    exercise = next((ex for ex in lesson.exercises if ex.id == payload.exercise_id), None)
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")

    is_correct = normalized_exercise_text(payload.answer) == normalized_exercise_text(
        exercise.correct_answer
    )

    if is_correct:
        message = _answer_feedback(user.native_language, "correct")
    else:
        message = _answer_feedback(
            user.native_language, "correct_answer", answer=exercise.correct_answer
        )

    return ExerciseFeedbackResponse(
        correct=is_correct,
        message=message,
        correct_answer=None if is_correct else exercise.correct_answer,
    )


@router.post("/{lesson_id}/exercise/pronunciation", response_model=PronunciationExerciseResponse)
async def pronunciation_exercise(
    lesson_id: int,
    payload: PronunciationExerciseRequest,
    user: User = Depends(lambda: None),  # placeholder
    db: AsyncSession = Depends(get_db),
):
    from app.models.lesson import Lesson

    lesson = await db.get(Lesson, lesson_id)
    if not lesson or lesson.study_plan.user_id != user.id:
        raise HTTPException(status_code=404, detail="Lesson not found")

    exercise = next((ex for ex in lesson.exercises if ex.id == payload.exercise_id), None)
    if not exercise or exercise.exercise_type != ExerciseType.PRONUNCIATION:
        raise HTTPException(status_code=404, detail="Pronunciation exercise not found")

    # Placeholder - real implementation would call STT and compare
    return PronunciationExerciseResponse(
        correct=True,
        message=_answer_feedback(user.native_language, "good_pronunciation"),
    )


@router.post("/{lesson_id}/submit", response_model=LessonSubmitResponse)
async def submit_lesson(
    lesson_id: int,
    payload: LessonSubmitRequest,
    user: User = Depends(lambda: None),  # placeholder
    db: AsyncSession = Depends(get_db),
):
    from app.models.lesson import Lesson
    from app.services.progress_service import update_daily_progress
    from app.services.progress_rewards import award_progress_reward
    from app.services.lesson_generator import lock_progress_plan

    lesson = await db.get(Lesson, lesson_id)
    if not lesson or lesson.study_plan.user_id != user.id:
        raise HTTPException(status_code=404, detail="Lesson not found")

    xp_earned = 0
    results = []

    for answer in payload.answers:
        exercise = next((ex for ex in lesson.exercises if ex.id == answer.exercise_id), None)
        if not exercise:
            continue

        is_correct = normalized_exercise_text(answer.answer) == normalized_exercise_text(
            exercise.correct_answer
        )
        results.append(
            {
                "exercise_id": exercise.id,
                "correct": is_correct,
                "message": _answer_feedback(
                    user.native_language,
                    "correct" if is_correct else "correct_answer",
                    answer=exercise.correct_answer,
                ),
            }
        )
        if is_correct:
            xp_earned += 10

    if xp_earned > 0:
        await update_daily_progress(user.id, xp_earned, db)
        await award_progress_reward(user.id, xp_earned, db)
        await lock_progress_plan(user.id, db)

    return LessonSubmitResponse(
        xp_earned=xp_earned,
        results=results,
        completed=len(results) == len(lesson.exercises),
    )


@router.get("/{plan_id}/progress", response_model=LessonProgressResponse)
async def lesson_progress(
    plan_id: int,
    user: User = Depends(lambda: None),  # placeholder
    db: AsyncSession = Depends(get_db),
):
    from app.models.study_plan import StudyPlan
    from app.models.lesson import Lesson
    from app.models.progress import LessonProgress

    plan = await db.get(StudyPlan, plan_id)
    if not plan or plan.user_id != user.id:
        raise HTTPException(status_code=404, detail="Study plan not found")

    lessons = (
        await db.execute(
            select(Lesson)
            .where(Lesson.study_plan_id == plan_id)
            .order_by(Lesson.order)
        )
    ).scalars().all()

    progress = []
    for lesson in lessons:
        completed = sum(1 for lp in lesson.progress if lp.user_id == user.id and lp.completed)
        total = len(lesson.exercises)
        progress.append(
            {
                "lesson_id": lesson.id,
                "title": lesson.title,
                "completed_exercises": completed,
                "total_exercises": total,
                "is_complete": completed == total and total > 0,
            }
        )

    return LessonProgressResponse(
        plan_id=plan_id,
        current_unit=plan.current_unit,
        lessons=progress,
    )
