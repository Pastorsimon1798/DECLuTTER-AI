import os

os.environ.setdefault("DECLUTTER_ENV", "test")

from services.trade_templates import (
    get_condition_checklist,
    get_message_templates,
    get_trade_rules,
)


def test_trade_message_templates():
    templates = get_message_templates("propose")
    assert len(templates) >= 3
    assert any("trade" in t.lower() for t in templates)

    accept_templates = get_message_templates("accept")
    assert len(accept_templates) >= 1

    decline_templates = get_message_templates("decline")
    assert len(decline_templates) >= 1

    follow_up_templates = get_message_templates("follow_up")
    assert len(follow_up_templates) >= 1

    unknown = get_message_templates("unknown")
    assert unknown == []


def test_condition_checklist():
    checklist = get_condition_checklist("good")
    assert "no major damage" in [c.lower() for c in checklist]
    assert isinstance(checklist, list)
    assert len(checklist) >= 3

    new_checklist = get_condition_checklist("new")
    assert len(new_checklist) >= 2

    unknown = get_condition_checklist("unknown")
    assert unknown == []


def test_trade_rules():
    rules = get_trade_rules()
    assert len(rules) >= 4
    assert any("trade value" in r.lower() for r in rules)
    assert any("condition" in r.lower() for r in rules)
