import os

os.environ.setdefault("DECLUTTER_ENV", "test")

from services.safety_checklists import get_all_checklists, get_safety_checklist


def test_electronics_safety():
    checklist = get_safety_checklist("electronics")
    assert "No frayed cords or exposed wiring" in checklist
    assert len(checklist) >= 3


def test_baby_safety():
    checklist = get_safety_checklist("baby")
    assert "No recalls issued (check CPSC.gov)" in checklist
    assert len(checklist) >= 3


def test_art_safety():
    checklist = get_safety_checklist("art")
    assert "Non-toxic label visible (if applicable)" in checklist


def test_unknown_tag_returns_empty():
    assert get_safety_checklist("unknown") == []


def test_all_checklists():
    all_checklists = get_all_checklists()
    assert "electronics" in all_checklists
    assert "baby" in all_checklists
    assert "plants" in all_checklists
    assert len(all_checklists) >= 8
