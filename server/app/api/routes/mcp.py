from fastapi import APIRouter

router = APIRouter(prefix="/agents/mcp", tags=["agents"])


@router.get("/capabilities")
def mcp_capabilities() -> dict[str, list[str]]:
    return {"tools": ["review_sessions", "generate_draft", "request_publish"]}
