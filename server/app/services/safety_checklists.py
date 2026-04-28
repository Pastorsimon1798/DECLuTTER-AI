"""Category-specific safety checklists for trade items.

Each checklist is tailored to the item type and covers the most common
safety concerns for that category.
"""


SAFETY_CHECKLISTS: dict[str, list[str]] = {
    "electronics": [
        "Works when plugged in",
        "No frayed cords or exposed wiring",
        "Battery holds charge (if applicable)",
        "No overheating or burning smell",
        "Screen intact (if applicable)",
    ],
    "baby": [
        "No recalls issued (check CPSC.gov)",
        "All straps/buckles intact and functional",
        "Clean, no stains or mold",
        "No loose or broken parts",
        "Meets current safety standards",
    ],
    "disability": [
        "Sanitized and clean",
        "All adjustment mechanisms work smoothly",
        "No rust or corrosion",
        "Padding intact (if applicable)",
        "All parts/hardware included",
    ],
    "art": [
        "Non-toxic label visible (if applicable)",
        "No dried-out tubes or containers",
        "Brushes not shedding bristles",
        "No strong chemical odors",
        "Sealed containers not leaking",
    ],
    "plants": [
        "No visible pests or eggs",
        "Potted in clean soil",
        "Acclimated to indoor conditions (if indoor plant)",
        "No signs of disease (yellowing, spots)",
        "Roots not rotting (if visible)",
    ],
    "books": [
        "No mold or water damage",
        "Pages intact and readable",
        "No strong odors",
        "Binding secure",
    ],
    "clothing": [
        "Clean and washed",
        "No stains or tears",
        "Zippers/buttons functional",
        "No strong odors or smoke smell",
    ],
    "games": [
        "All pieces accounted for",
        "No broken or damaged components",
        "Box intact (if applicable)",
        "Instructions included (if applicable)",
    ],
    "sports": [
        "No cracks or structural damage",
        "Padding intact (helmets, pads)",
        "Clean and dry",
        "No rust on metal parts",
    ],
    "music": [
        "All strings/keys functional",
        "No cracks in body",
        "Electronics work (if applicable)",
        "Clean and dust-free",
    ],
}


def get_safety_checklist(tag: str) -> list[str]:
    """Return safety checklist for a given item tag/category."""
    return SAFETY_CHECKLISTS.get(tag.lower(), [])


def get_all_checklists() -> dict[str, list[str]]:
    """Return all available safety checklists."""
    return dict(SAFETY_CHECKLISTS)
