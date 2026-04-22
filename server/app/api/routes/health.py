from fastapi import APIRouter

from core.settings import Settings

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/readiness")
def readiness() -> dict[str, object]:
    state = Settings.readiness()
    return {
        "self_hosted_mvp_ready": state.self_hosted_mvp_ready,
        "ready_for_production": state.ready_for_production,
        "checks": {
            "shared_token_auth_configured": state.shared_token_auth_configured,
            "local_upload_storage_configured": state.local_upload_storage_configured,
            "sqlite_session_store_configured": state.sqlite_session_store_configured,
            "home_inference_configured": state.home_inference_configured,
            "firebase_admin_configured": state.firebase_admin_configured,
            "cloud_storage_configured": state.cloud_storage_configured,
            "multimodal_model_configured": state.multimodal_model_configured,
            "ebay_api_configured": state.ebay_api_configured,
        },
    }
