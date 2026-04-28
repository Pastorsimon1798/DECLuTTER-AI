"""NeuroDivergent-friendly trade templates and structured interactions.

Design principles:
- Literal, explicit language (no idioms, no ambiguity)
- Fixed options instead of free-text where possible
- Async-friendly (no real-time negotiation pressure)
- Clear expectations at every step
"""


MESSAGE_TEMPLATES = {
    "propose": [
        "I would like to propose a trade for your [item]. I have [my item] valued at [value]. Would you be interested?",
        "I am interested in your [item]. I can offer [my item] plus [credit amount] credits. Let me know if this works.",
        "I would like to trade [my item] for your [item]. Both are valued at approximately [value]. Would you accept?",
    ],
    "accept": [
        "I accept your trade proposal. I will prepare the item for pickup/shipping.",
        "Trade accepted. Please let me know your preferred pickup time or shipping address.",
    ],
    "decline": [
        "Thank you for your interest, but I am not interested in this trade at this time.",
        "I appreciate the offer, but I am looking for different items right now.",
    ],
    "follow_up": [
        "Just checking in — are you still interested in our trade?",
        "I have the item ready. When would be a good time to meet?",
    ],
}


CONDITION_CHECKLISTS = {
    "new": [
        "Item is unopened or unused",
        "Original packaging intact",
        "No signs of wear",
    ],
    "like_new": [
        "Item used once or twice only",
        "No visible wear",
        "All parts/pieces included",
        "Original packaging available",
    ],
    "good": [
        "Item functions perfectly",
        "Minor cosmetic wear only",
        "No major damage",
        "All essential parts included",
    ],
    "fair": [
        "Item functions but has visible wear",
        "Some cosmetic damage",
        "May be missing non-essential parts",
        "Still usable",
    ],
    "for_parts": [
        "Item does not function fully",
        "Significant damage or wear",
        "Useful for parts, repair, or craft projects",
        "Condition clearly described",
    ],
}


TRADE_RULES = [
    "Both parties agree to the trade value shown.",
    "Items must match the described condition.",
    "Pickup or shipping must be arranged within 7 days.",
    "If using credits, the balance is deducted immediately upon acceptance.",
    "Either party can cancel before acceptance with no penalty.",
    "After acceptance, the trade is final.",
]


def get_message_templates(intent: str) -> list[str]:
    return MESSAGE_TEMPLATES.get(intent, [])


def get_condition_checklist(condition: str) -> list[str]:
    return CONDITION_CHECKLISTS.get(condition, [])


def get_trade_rules() -> list[str]:
    return TRADE_RULES
