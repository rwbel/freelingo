"""
Asturian curriculum — assembles all CEFR levels.
"""

from __future__ import annotations

from app.data._types import CEFRLevel, CurriculumUnit, LessonType  # noqa: F401
from app.data.ast.curriculum_a1 import A1_UNITS
from app.data.ast.curriculum_a2 import A2_UNITS
from app.data.ast.curriculum_b1 import B1_UNITS
from app.data.ast.curriculum_b2 import B2_UNITS
from app.data.ast.curriculum_c1 import C1_UNITS
from app.data.ast.curriculum_c2 import C2_UNITS
from app.data.curriculum import distribute_units as _distribute_units

CEFR_LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"]

CURRICULUM: dict[str, list[CurriculumUnit]] = {
    "A1": A1_UNITS,
    "A2": A2_UNITS,
    "B1": B1_UNITS,
    "B2": B2_UNITS,
    "C1": C1_UNITS,
    "C2": C2_UNITS,
}

INTENSITY_CONFIG = {
    "intensive": {"duration_weeks": 4, "days_per_week": 6},
    "standard": {"duration_weeks": 8, "days_per_week": 4},
    "relaxed": {"duration_weeks": 16, "days_per_week": 3},
    "very_relaxed": {"duration_weeks": 24, "days_per_week": 2},
}


def get_curriculum_units(level: str) -> list[CurriculumUnit]:
    return CURRICULUM.get(level, [])


def distribute_units(
    units: list[CurriculumUnit], total_weeks: int, days_per_week: int
) -> list[dict]:
    # Use the main distribute_units with target_language="ast-ES" for proper i18n
    return _distribute_units(units, total_weeks, days_per_week, target_language="ast-ES")
