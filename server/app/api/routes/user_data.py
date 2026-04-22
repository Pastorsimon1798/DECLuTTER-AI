from fastapi import APIRouter

router = APIRouter(prefix="/user-data", tags=["privacy"])


@router.delete("/me")
def delete_my_data() -> dict[str, str]:
    return {"status": "queued", "message": "Deletion workflow scaffolded."}
