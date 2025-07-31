from fastapi import APIRouter

router = APIRouter()

# 서버 동작 체크
@router.get("/api/healthz")
def health_check():
    return {"status": "ok"}