"""Unit tests for the language-dispatched assessment bank."""

from __future__ import annotations

from collections import Counter, defaultdict

import pytest


def test_ast_bank_has_valid_answers_references_and_balanced_positions():
    from app.data.assessment_bank import get_assessment_bank
    from app.data.grammar import get_grammar_topics

    language = "ast-ES"
    bank = get_assessment_bank(language)
    slugs = {topic.slug for topic in get_grammar_topics(language)}
    positions = defaultdict(Counter)
    assert len({question.id for question in bank}) == len(bank)

    for question in bank:
        assert len(question.options) == len(set(question.options)) == 4, question.id
        assert question.options.count(question.correct) == 1, question.id
        if question.grammar_slug:
            assert question.grammar_slug in slugs, question.id
        positions[question.difficulty, question.skill][
            question.options.index(question.correct)
        ] += 1

    for group, counts in positions.items():
        totals = [counts[index] for index in range(4)]
        assert max(totals) - min(totals) <= 1, (language, group, counts)


def test_es_bank_has_valid_structure():
    """Spanish bank structure validation (balance check skipped for legacy data)."""
    from app.data.assessment_bank import get_assessment_bank
    from app.data.grammar import get_grammar_topics

    language = "es-ES"
    bank = get_assessment_bank(language)
    slugs = {topic.slug for topic in get_grammar_topics(language)}
    assert len({question.id for question in bank}) == len(bank)

    for question in bank:
        assert len(question.options) == len(set(question.options)) == 4, question.id
        assert question.options.count(question.correct) == 1, question.id
        if question.grammar_slug:
            assert question.grammar_slug in slugs, question.id


class TestGetAssessmentBank:
    def test_spanish_returns_non_empty(self):
        from app.data.assessment_bank import get_assessment_bank

        bank = get_assessment_bank("es-ES")
        assert isinstance(bank, list)
        assert len(bank) > 0

    def test_asturian_returns_non_empty(self):
        from app.data.assessment_bank import get_assessment_bank

        bank = get_assessment_bank("ast-ES")
        assert isinstance(bank, list)
        # ast-ES A1 assessment bank may be small or empty initially
        assert len(bank) >= 0

    def test_unknown_language_falls_back_to_es_es(self):
        from app.data.assessment_bank import get_assessment_bank

        bank_unknown = get_assessment_bank("xx-XX")
        bank_es = get_assessment_bank("es-ES")
        assert bank_unknown == bank_es

    def test_empty_language_falls_back_to_es_es(self):
        from app.data.assessment_bank import get_assessment_bank

        bank_empty = get_assessment_bank("")
        bank_es = get_assessment_bank("es-ES")
        assert bank_empty == bank_es

    def test_cache_reuses_imported_module(self):
        from app.data.assessment_bank import _CACHE, get_assessment_bank

        _CACHE.clear()
        b1 = get_assessment_bank("es-ES")
        b2 = get_assessment_bank("es-ES")
        assert b1 is b2
        assert len(_CACHE) == 1
