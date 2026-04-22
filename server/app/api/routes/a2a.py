from fastapi import APIRouter

router = APIRouter(prefix="/agents/a2a", tags=["agents"])


@router.get("/card")
def a2a_card() -> dict[str, str]:
    return {"name": "DECLuTTER-AI Buyer Agent", "status": "stub"}
