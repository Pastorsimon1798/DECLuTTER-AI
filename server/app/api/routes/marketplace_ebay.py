from fastapi import APIRouter

router = APIRouter(prefix="/marketplace/ebay", tags=["marketplace"])


@router.get("/status")
def ebay_status() -> dict[str, str]:
    return {"provider": "ebay", "status": "not_connected"}
