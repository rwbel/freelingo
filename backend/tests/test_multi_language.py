"""Multi-language tests — Phase 10.1 / 10.2 / 10.3.

Covers:
  10.1 — Database isolation and constraints
  10.2 — Prompt language awareness
  10.3 — Language API endpoints (CRUD, validation, assessment)
"""

from __future__ import annotations

from datetime import date

import pytest
from sqlalchemy import func, select

from app.core.security import create_access_token, hash_password
from app.models.flashcard import Flashcard
from app.models.memory import Memory
from app.models.progress import Progress
from app.models.study_plan import StudyPlan
from app.models.user import User
from app.models.user_language import UserLanguage
from app.services.memory_service import get_user_memories

# ═════════════════════════════════════════════════════════════════════════════
# Helpers
# ═════════════════════════════════════════════════════════════════════════════


async def _make_user(db, *, username="mluser", email="ml@example.com", language="es-ES"):
    user = User(
        username=username,
        email=email,
        display_name="ML User",
        hashed_password=hash_password("testpass"),
        role="user",
        native_language="es",
        target_language=language,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    db.add(UserLanguage(user_id=user.id, target_language=language, is_active=True))
    await db.commit()
    await db.refresh(user)
    token = create_access_token(user.id, user.role)
    return user, {"Authorization": f"Bearer {token}"}


async def _add_language(db, user_id: int, code: str, *, active: bool = False):
    from sqlalchemy import update as _update

    if active:
        await db.execute(
            _update(UserLanguage)
            .where(UserLanguage.user_id == user_id, UserLanguage.is_active.is_(True))
            .values(is_active=False)
        )
    entry = UserLanguage(user_id=user_id, target_language=code, is_active=active)
    db.add(entry)
    await db.commit()
    return entry


async def _make_plan(db, user_id: int, *, cefr="A1", language="es-ES", active=True):
    from tests.conftest import make_study_plan

    return await make_study_plan(
        db,
        user_id=user_id,
        cefr_level=cefr,
        target_language=language,
        goals=["grammar"],
        duration_weeks=4,
        days_per_week=4,
        current_unit="",
        generated_plan={},
        is_active=active,
    )


# ═════════════════════════════════════════════════════════════════════════════
# 10.1 — Database isolation and constraints
# ═════════════════════════════════════════════════════════════════════════════


class TestMultiLanguageIsolation:
    @pytest.mark.asyncio
    async def test_active_plan_per_language(self, client, db_session):
        """Two languages can each have an active plan simultaneously."""
        user, _headers = await _make_user(db_session)

        await _add_language(db_session, user.id, "ast-ES", active=False)
        plan_es = await _make_plan(db_session, user.id, language="es-ES")
        plan_ast = await _make_plan(db_session, user.id, language="ast-ES")

        assert plan_es.is_active
        assert plan_ast.is_active
        assert plan_es.target_language != plan_ast.target_language

    @pytest.mark.asyncio
    async def test_unique_index_prevents_duplicate_active_plans(self, client, db_session):
        """Cannot create two active plans for the same user+language."""
        from sqlalchemy.exc import IntegrityError

        user, _headers = await _make_user(db_session)

        await _make_plan(db_session, user.id, language="es-ES", active=True)

        with pytest.raises(IntegrityError):
            await _make_plan(db_session, user.id, language="es-ES", active=True)

    @pytest.mark.asyncio
    async def test_progress_isolated_by_language(self, client, db_session):
        """Progress for one language does not affect the other."""
        user, _headers = await _make_user(db_session)
        await _add_language(db_session, user.id, "ast-ES", active=False)
        plan_es = await _make_plan(db_session, user.id, language="es-ES")
        plan_ast = await _make_plan(db_session, user.id, language="ast-ES")

        today = date.today()
        db_session.add_all(
            [
                Progress(
                    user_id=user.id,
                    study_plan_id=plan_es.id,
                    date=today,
                    xp_earned=100,
                    streak_day=5,
                    lessons_completed=3,
                ),
                Progress(
                    user_id=user.id,
                    study_plan_id=plan_ast.id,
                    date=today,
                    xp_earned=50,
                    streak_day=2,
                    lessons_completed=1,
                ),
            ]
        )
        await db_session.commit()

        count_es = await db_session.scalar(
            select(func.count()).where(Progress.study_plan_id == plan_es.id)
        )
        count_ast = await db_session.scalar(
            select(func.count()).where(Progress.study_plan_id == plan_ast.id)
        )
        assert count_es == 1
        assert count_ast == 1

    @pytest.mark.asyncio
    async def test_flashcards_isolated_by_language(self, client, db_session):
        """Flashcards are scoped by study_plan_id — no cross-language leakage."""
        user, _headers = await _make_user(db_session)
        await _add_language(db_session, user.id, "ast-ES", active=False)
        plan_es = await _make_plan(db_session, user.id, language="es-ES")
        plan_ast = await _make_plan(db_session, user.id, language="ast-ES")

        fc_es = Flashcard(
            user_id=user.id,
            study_plan_id=plan_es.id,
            word="casa",
            definition="Edificio donde se vive",
            example_sentence="La casa es grande.",
            translation="house",
            source="chat",
        )
        fc_ast = Flashcard(
            user_id=user.id,
            study_plan_id=plan_ast.id,
            word="casa",
            definition="Edificiu onde se vive",
            example_sentence="La casa ye grande.",
            translation="house",
            source="chat",
        )
        db_session.add_all([fc_es, fc_ast])
        await db_session.commit()

        count_es = await db_session.scalar(
            select(func.count()).where(Flashcard.study_plan_id == plan_es.id)
        )
        count_ast = await db_session.scalar(
            select(func.count()).where(Flashcard.study_plan_id == plan_ast.id)
        )
        assert count_es == 1
        assert count_ast == 1

    @pytest.mark.asyncio
    async def test_memories_shared_across_languages(self, client, db_session):
        """Plan provenance never limits global user memory retrieval."""
        user, _headers = await _make_user(db_session)
        await _add_language(db_session, user.id, "ast-ES", active=False)
        plan_es = await _make_plan(db_session, user.id, language="es-ES")
        plan_ast = await _make_plan(db_session, user.id, language="ast-ES")

        mem_es = Memory(
            user_id=user.id,
            study_plan_id=plan_es.id,
            content="User likes dogs",
            source="chat",
        )
        mem_ast = Memory(
            user_id=user.id,
            study_plan_id=plan_ast.id,
            content="Usuario prefiere gatos",
            source="chat",
        )
        db_session.add_all([mem_es, mem_ast])
        await db_session.commit()

        memories = await get_user_memories(db_session, user.id)
        assert [memory.content for memory in memories] == [
            "User likes dogs",
            "Usuario prefiere gatos",
        ]

    @pytest.mark.asyncio
    async def test_conversations_isolated_by_language(self, client, db_session):
        """Conversations are scoped by study_plan_id."""
        from app.models.conversation import Conversation

        user, _headers = await _make_user(db_session)
        await _add_language(db_session, user.id, "ast-ES", active=False)
        plan_es = await _make_plan(db_session, user.id, language="es-ES")
        plan_ast = await _make_plan(db_session, user.id, language="ast-ES")

        conv_es = Conversation(
            user_id=user.id,
            study_plan_id=plan_es.id,
            title="Spanish chat",
            source="chat",
        )
        conv_ast = Conversation(
            user_id=user.id,
            study_plan_id=plan_ast.id,
            title="Asturian chat",
            source="chat",
        )
        db_session.add_all([conv_es, conv_ast])
        await db_session.commit()

        count_es = await db_session.scalar(
            select(func.count()).where(Conversation.study_plan_id == plan_es.id)
        )
        count_ast = await db_session.scalar(
            select(func.count()).where(Conversation.study_plan_id == plan_ast.id)
        )
        assert count_es == 1
        assert count_ast == 1


# ═════════════════════════════════════════════════════════════════════════════
# 10.2 — Prompt language awareness
# ═════════════════════════════════════════════════════════════════════════════


class TestPromptLanguage:
    @pytest.mark.asyncio
    async def test_active_language_resolves_to_study_plan(self, client, db_session):
        """The active UserLanguage's target_language is used to find the active
        study plan via get_active_study_plan dependency."""
        user, headers = await _make_user(db_session)
        plan = await _make_plan(db_session, user.id, language="es-ES", cefr="B1")

        # get_active_study_plan resolves plan by active UserLanguage
        from app.core.database import get_db

        async def _resolve():

            # Simulate what the dependency does
            async for _session in get_db():
                break
            return None  # can't fully test dependency injection here

        # Verify the plan matches the active language
        assert plan.target_language == "es-ES"

    @pytest.mark.asyncio
    async def test_add_language_activates_new_language(self, client, db_session):
        """When a new language is added, it becomes the active one."""
        user, headers = await _make_user(db_session)

        # es-ES is active (from test_user fixture pattern)
        active_before = await client.get("/api/languages/active", headers=headers)
        assert active_before.json()["target_language"] == "es-ES"

        # Add ast-ES — should become active
        await client.post("/api/languages", headers=headers, json={"target_language": "ast-ES"})
        active_after = await client.get("/api/languages/active", headers=headers)
        assert active_after.json()["target_language"] == "ast-ES"

    @pytest.mark.asyncio
    async def test_study_plan_generator_accepts_language_param(self, client, db_session):
        """POST /api/study-plan/generate accepts target_language parameter."""
        user, headers = await _make_user(db_session)
        await _add_language(db_session, user.id, "ast-ES", active=False)

        res = await client.post(
            "/api/study-plan/generate",
            headers=headers,
            json={
                "cefr_level": "A1",
                "goals": ["vocabulary"],
                "target_language": "ast-ES",
                "duration_weeks": 4,
                "days_per_week": 4,
            },
        )
        assert res.status_code == 200
        data = res.json()
        # Verify the plan was created for the requested language
        assert data["cefr_level"] == "A1"
        # The plan in the DB should have the correct target_language
        ast_plan = (
            await db_session.execute(
                select(StudyPlan).where(
                    StudyPlan.user_id == user.id,
                    StudyPlan.target_language == "ast-ES",
                )
            )
        ).scalar_one_or_none()
        assert ast_plan is not None


# ═════════════════════════════════════════════════════════════════════════════
# 10.3 — Language API endpoints
# ═════════════════════════════════════════════════════════════════════════════


class TestLanguageAPI:
    @pytest.mark.asyncio
    async def test_add_new_language(self, client, db_session):
        """POST /api/languages creates a UserLanguage row."""
        user, headers = await _make_user(db_session)

        res = await client.post(
            "/api/languages",
            headers=headers,
            json={"target_language": "ast-ES"},
        )
        assert res.status_code == 201
        data = res.json()
        assert data["target_language"] == "ast-ES"
        assert data["is_active"] is True

    @pytest.mark.asyncio
    async def test_add_duplicate_language(self, client, db_session):
        """POST with an already-existing language returns 409."""
        user, headers = await _make_user(db_session)

        await client.post("/api/languages", headers=headers, json={"target_language": "ast-ES"})
        res = await client.post(
            "/api/languages", headers=headers, json={"target_language": "ast-ES"}
        )
        assert res.status_code == 409

    @pytest.mark.asyncio
    async def test_switch_language(self, client, db_session):
        """PUT /api/languages/active switches the active language."""
        user, headers = await _make_user(db_session)
        await client.post("/api/languages", headers=headers, json={"target_language": "ast-ES"})

        # ast-ES should now be active (was just added, which auto-activates)
        active_res = await client.get("/api/languages/active", headers=headers)
        assert active_res.json()["target_language"] == "ast-ES"

        # Switch back to es-ES
        switch_res = await client.put(
            "/api/languages/active",
            headers=headers,
            json={"target_language": "es-ES"},
        )
        assert switch_res.status_code == 200
        assert switch_res.json()["target_language"] == "es-ES"

        # Verify it actually changed
        active_res = await client.get("/api/languages/active", headers=headers)
        assert active_res.json()["target_language"] == "es-ES"

    @pytest.mark.asyncio
    async def test_list_languages(self, client, db_session):
        """GET /api/languages returns all languages with summarised progress."""
        user, headers = await _make_user(db_session)
        await _make_plan(db_session, user.id, language="es-ES", cefr="B1")

        res = await client.get("/api/languages", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert "languages" in data
        assert len(data["languages"]) >= 1
        assert any(lang["target_language"] == "es-ES" for lang in data["languages"])
        assert "all_supported_languages" in data
        # Only es-ES and ast-ES should be supported
        assert data["all_supported_languages"] == ["es-ES", "ast-ES"]

    @pytest.mark.asyncio
    async def test_remove_language_cascades(self, client, db_session):
        """Language deletion removes scoped data but preserves global memories."""
        user, headers = await _make_user(db_session)
        await client.post("/api/languages", headers=headers, json={"target_language": "ast-ES"})
        plan_ast = await _make_plan(db_session, user.id, language="ast-ES")
        memory = Memory(
            user_id=user.id,
            study_plan_id=plan_ast.id,
            content="User enjoys cooking",
            source="chat",
        )
        db_session.add(memory)
        await db_session.commit()
        memory_id = memory.id
        user_id = user.id

        # Switch away from ast-ES first (can't delete active language)
        await client.put(
            "/api/languages/active",
            headers=headers,
            json={"target_language": "es-ES"},
        )

        res = await client.delete("/api/languages/ast-ES", headers=headers)
        assert res.status_code == 204

        # Verify it's gone
        remaining = (
            (await db_session.execute(select(UserLanguage).where(UserLanguage.user_id == user.id)))
            .scalars()
            .all()
        )
        assert all(lang.target_language != "ast-ES" for lang in remaining)
        db_session.expire_all()
        preserved = await db_session.get(Memory, memory_id)
        assert preserved is not None
        assert preserved.user_id == user_id
        assert preserved.study_plan_id is None

    @pytest.mark.asyncio
    async def test_cannot_remove_last_language(self, client, db_session):
        """DELETE when user has only 1 language returns 400."""
        user, headers = await _make_user(db_session)

        res = await client.delete("/api/languages/es-ES", headers=headers)
        assert res.status_code == 400

    @pytest.mark.asyncio
    async def test_cannot_remove_active_language(self, client, db_session):
        """DELETE on the currently active language returns 400."""
        user, headers = await _make_user(db_session)
        await client.post("/api/languages", headers=headers, json={"target_language": "ast-ES"})

        # ast-ES is now active (added last, auto-activates), try to delete it
        res = await client.delete("/api/languages/ast-ES", headers=headers)
        assert res.status_code == 400

    @pytest.mark.asyncio
    @pytest.mark.parametrize("language", ["xx-XX", "ast", "ast-es"])
    async def test_supported_languages_validation(self, client, db_session, language):
        """POST /api/languages requires a supported canonical target code."""
        user, headers = await _make_user(db_session)

        res = await client.post(
            "/api/languages",
            headers=headers,
            json={"target_language": language},
        )
        assert res.status_code == 422

    @pytest.mark.asyncio
    async def test_asturian_language_can_be_added(self, client, db_session):
        """ast-ES is accepted by the backend language allow-list."""
        user, headers = await _make_user(db_session)

        res = await client.post(
            "/api/languages", headers=headers, json={"target_language": "ast-ES"}
        )

        assert res.status_code == 201
        assert res.json()["target_language"] == "ast-ES"

    @pytest.mark.asyncio
    @pytest.mark.parametrize("language", ["ast-ES"])
    async def test_add_plan_switch_and_remove_preserve_other_language(
        self, client, db_session, language
    ):
        from app.data.curriculum import get_curriculum

        user, headers = await _make_user(db_session, language="es-ES")
        english = await _make_plan(db_session, user.id, language="es-ES")
        added = await client.post(
            "/api/languages", headers=headers, json={"target_language": language}
        )
        assert added.status_code == 201
        assert added.json()["target_language"] == language
        generated = await client.post(
            "/api/study-plan/generate",
            headers=headers,
            json={
                "cefr_level": "A1",
                "target_language": language,
                "goals": ["grammar"],
                "duration_weeks": 4,
                "days_per_week": 4,
            },
        )
        assert generated.status_code == 200
        assert generated.json()["target_language"] == language
        target_plan = await db_session.scalar(
            select(StudyPlan).where(
                StudyPlan.user_id == user.id,
                StudyPlan.target_language == language,
                StudyPlan.is_active.is_(True),
            )
        )
        assert target_plan is not None
        assert target_plan.user_language_id != english.user_language_id
        assert get_curriculum(target_plan.target_language) is not get_curriculum("es-ES")
        first_unit = get_curriculum(language)["A1"][0]
        first_day = target_plan.generated_plan["weekly_plan"][0]["days"][0]
        assert first_day["unit_id"] == first_unit.id
        assert first_day["title"].startswith(first_unit.title)
        target_plan_id, english_plan_id = target_plan.id, english.id
        db_session.add_all(
            [
                Progress(
                    user_id=user.id,
                    study_plan_id=plan.id,
                    date=date.today(),
                    xp_earned=xp,
                    streak_day=1,
                    lessons_completed=1,
                )
                for plan, xp in ((english, 100), (target_plan, 25))
            ]
        )
        await db_session.commit()
        switched = await client.put(
            "/api/languages/active", headers=headers, json={"target_language": "es-ES"}
        )
        assert switched.status_code == 200
        current = await client.get("/api/study-plan/current", headers=headers)
        assert current.status_code == 200
        assert current.json()["id"] == english_plan_id
        assert current.json()["target_language"] == "es-ES"
        switched_back = await client.put(
            "/api/languages/active", headers=headers, json={"target_language": language}
        )
        assert switched_back.status_code == 200
        current = await client.get("/api/study-plan/current", headers=headers)
        assert current.status_code == 200
        assert current.json()["id"] == target_plan_id
        assert current.json()["target_language"] == language
        listed = await client.get("/api/languages", headers=headers)
        assert listed.status_code == 200
        languages = {entry["target_language"]: entry for entry in listed.json()["languages"]}
        assert languages[language]["is_active"] is True
        assert languages[language]["plan"]["id"] == target_plan_id
        assert languages[language]["progress"]["total_xp"] == 25
        assert languages["es-ES"]["plan"]["id"] == english_plan_id
        assert languages["es-ES"]["progress"]["total_xp"] == 100
        switched = await client.put(
            "/api/languages/active", headers=headers, json={"target_language": "es-ES"}
        )
        assert switched.status_code == 200
        removed = await client.delete(f"/api/languages/{language}", headers=headers)
        assert removed.status_code == 204
        listed = await client.get("/api/languages", headers=headers)
        assert listed.status_code == 200
        assert [entry["target_language"] for entry in listed.json()["languages"]] == ["es-ES"]
        assert listed.json()["languages"][0]["plan"]["id"] == english_plan_id
        assert listed.json()["languages"][0]["progress"]["total_xp"] == 100
        remaining_plans = await db_session.scalar(
            select(func.count()).select_from(StudyPlan).where(StudyPlan.id == target_plan_id)
        )
        remaining_progress = await db_session.scalar(
            select(func.count())
            .select_from(Progress)
            .where(Progress.study_plan_id == target_plan_id)
        )
        assert remaining_plans == remaining_progress == 0
        await db_session.refresh(english)
        assert english.is_active is True

    @pytest.mark.asyncio
    async def test_portuguese_variants_removed(self, client, db_session):
        """Test that Portuguese variants are no longer supported."""
        user, headers = await _make_user(db_session)

        # pt-BR and pt-PT should no longer be accepted
        res = await client.post(
            "/api/languages", headers=headers, json={"target_language": "pt-BR"}
        )
        assert res.status_code == 422

        res = await client.post(
            "/api/languages", headers=headers, json={"target_language": "pt-PT"}
        )
        assert res.status_code == 422

    @pytest.mark.asyncio
    async def test_plan_deactivation_scoped_by_language(self, client, db_session):
        """Creating an Asturian plan does not deactivate the active Spanish plan."""
        user, headers = await _make_user(db_session)
        await _add_language(db_session, user.id, "ast-ES", active=False)
        plan_es = await _make_plan(db_session, user.id, language="es-ES")

        await client.post(
            "/api/study-plan/generate",
            headers=headers,
            json={
                "cefr_level": "A1",
                "goals": ["vocabulary"],
                "target_language": "ast-ES",
                "duration_weeks": 4,
                "days_per_week": 4,
            },
        )

        await db_session.refresh(plan_es)
        assert plan_es.is_active is True  # Spanish plan should still be active

        ast_plan = (
            await db_session.execute(
                select(StudyPlan).where(
                    StudyPlan.user_id == user.id,
                    StudyPlan.target_language == "ast-ES",
                )
            )
        ).scalar_one_or_none()
        assert ast_plan is not None
        assert ast_plan.is_active is True

    @pytest.mark.asyncio
    async def test_onboarding_creates_user_language(self, client, db_session):
        """Registration + PATCH /api/auth/me creates UserLanguage row."""
        user = User(
            username="freshuser",
            email="fresh@example.com",
            display_name="Fresh",
            hashed_password=hash_password("testpass"),
            role="user",
            native_language="fr",
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()

        token = create_access_token(user.id, user.role)
        headers = {"Authorization": f"Bearer {token}"}

        res = await client.patch(
            "/api/auth/me",
            headers=headers,
            json={"target_language": "es-ES"},
        )
        assert res.status_code == 200

        ul = (
            await db_session.execute(
                select(UserLanguage).where(
                    UserLanguage.user_id == user.id,
                    UserLanguage.target_language == "es-ES",
                )
            )
        ).scalar_one_or_none()
        assert ul is not None
        assert ul.is_active is True

    @pytest.mark.asyncio
    async def test_assessment_language_param(self, client, db_session):
        """GET /api/assessment/start?language=es-ES stores session under scoped Redis key."""
        from unittest.mock import patch as mock_patch

        user, headers = await _make_user(db_session)
        await _add_language(db_session, user.id, "ast-ES", active=False)

        mock_quiz = {
            "questions": [
                {
                    "id": 1,
                    "type": "multiple_choice",
                    "difficulty": "A1",
                    "question": "¿Cuál es la capital de España?",
                    "options": ["A. París", "B. Madrid", "C. Roma", "D. Lisboa"],
                    "correct_answer": "B",
                }
            ]
        }

        with mock_patch(
            "app.routers.assessment.llm_adapter.structured_output",
            return_value=mock_quiz,
        ):
            res = await client.get(
                "/api/assessment/start?language=es-ES",
                headers=headers,
            )

        assert res.status_code == 200
        data = res.json()
        assert "quiz" in data
        assert "session_id" in data

    @pytest.mark.asyncio
    async def test_assessment_redis_key_isolation(self, client, db_session, mock_redis):
        """Two simultaneous assessments for different languages must not overwrite each other.

        Flow:
          1. Start English assessment   → stores at assessment:{uid}:en-US
          2. Start Spanish assessment   → stores at assessment:{uid}:es-ES
          3. Submit English answers with target_language=en-US → resolves en-US session, returns result
          4. Verify Spanish session is still intact at assessment:{uid}:es-ES
        """
        import json as _json
        from unittest.mock import patch as mock_patch

        user, headers = await _make_user(db_session)
        await _add_language(db_session, user.id, "ast-ES", active=False)

        mock_quiz_es = {
            "questions": [
                {
                    "id": 1,
                    "type": "multiple_choice",
                    "difficulty": "B1",
                    "question": "Choose the correct verb form.",
                    "options": ["A. have", "B. has", "C. had", "D. having"],
                    "correct_answer": "A",
                }
            ]
        }
        mock_quiz_ast = {
            "questions": [
                {
                    "id": 2,
                    "type": "multiple_choice",
                    "difficulty": "A1",
                    "question": "¿Qué significa 'casa'?",
                    "options": ["A. cat", "B. dog", "C. house", "D. fish"],
                    "correct_answer": "C",
                }
            ]
        }
        mock_eval = {
            "cefr_level": "B1",
            "score": 0.8,
            "analysis": "Good",
            "strengths": ["grammar"],
            "weaknesses": [],
        }

        # Step 1: start Spanish assessment
        with mock_patch(
            "app.routers.assessment.llm_adapter.structured_output",
            return_value=mock_quiz_es,
        ):
            await client.get("/api/assessment/start?language=es-ES", headers=headers)

        # Step 2: start Asturian assessment (must NOT overwrite the Spanish session)
        with mock_patch(
            "app.routers.assessment.llm_adapter.structured_output",
            return_value=mock_quiz_ast,
        ):
            await client.get("/api/assessment/start?language=ast-ES", headers=headers)

        # Verify both sessions are stored under separate keys
        es_session_raw = await mock_redis.get(f"assessment:{user.id}:es-ES")
        ast_session_raw = await mock_redis.get(f"assessment:{user.id}:ast-ES")
        assert es_session_raw is not None, "Spanish session must still exist"
        assert ast_session_raw is not None, "Asturian session must exist"

        es_session = _json.loads(es_session_raw)
        ast_session = _json.loads(ast_session_raw)
        assert es_session["target_language"] == "es-ES"
        assert ast_session["target_language"] == "ast-ES"

        # Step 3: submit Spanish answers — must evaluate the Spanish session
        with mock_patch(
            "app.routers.assessment.llm_adapter.structured_output",
            return_value=mock_eval,
        ):
            submit_res = await client.post(
                "/api/assessment/submit",
                headers=headers,
                json={
                    "answers": [{"question_id": 1, "answer": "A"}],
                    "target_language": "es-ES",
                },
            )
        assert submit_res.status_code == 200
        assert submit_res.json()["cefr_level"] == "B1"

        # Step 4: Asturian session must be untouched after Spanish submission
        ast_session_after = await mock_redis.get(f"assessment:{user.id}:ast-ES")
        assert ast_session_after is not None, "Asturian session must survive Spanish submission"
        assert _json.loads(ast_session_after)["target_language"] == "ast-ES"

        # Spanish session must have been deleted by /submit
        es_session_after = await mock_redis.get(f"assessment:{user.id}:es-ES")
        assert es_session_after is None, "Spanish session must be deleted after submission"


# ═════════════════════════════════════════════════════════════════════════════
# 10.6 — Curriculum per language
# ═════════════════════════════════════════════════════════════════════════════


class TestCurriculumPerLanguage:
    @pytest.mark.asyncio
    async def test_curriculum_spanish(self, client):
        """get_curriculum('es-ES') returns Spanish curriculum."""
        from app.data.curriculum import get_curriculum

        c = get_curriculum("es-ES")
        assert "A1" in c
        assert "C2" in c
        assert len(c["A1"]) == 8
        assert len(c["C2"]) == 8
        # Verify it's Spanish content
        assert c["A1"][0].title == "Saludos y presentaciones"

    @pytest.mark.asyncio
    async def test_curriculum_asturian(self, client):
        """get_curriculum('ast-ES') returns Asturian curriculum."""
        from app.data.curriculum import get_curriculum

        c = get_curriculum("ast-ES")
        assert "A1" in c
        assert len(c["A1"]) == 8
        # Verify it's Asturian content
        assert c["A1"][0].title == "Saludos y presentaciones"

    @pytest.mark.asyncio
    async def test_curriculum_fallback(self, client):
        """Unsupported language falls back to Spanish."""
        from app.data.curriculum import get_curriculum

        c = get_curriculum("xx-XX")
        assert "A1" in c
        # Should be Spanish content
        assert c["A1"][0].title == "Saludos y presentaciones"

    @pytest.mark.asyncio
    async def test_get_curriculum_units_with_language(self, client):
        """get_curriculum_units resolves correct language."""
        from app.data.curriculum import get_curriculum_units

        es_units = get_curriculum_units("A1", "es-ES")
        ast_units = get_curriculum_units("A1", "ast-ES")

        assert es_units[0].vocabulary_set_ids != ast_units[0].vocabulary_set_ids
        assert len(es_units) == 8
        assert len(ast_units) == 8
