from fastapi import APIRouter

router = APIRouter()

@router.get("/api/healthz")
def health_check():
    return {"status": "ok"}