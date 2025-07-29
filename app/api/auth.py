from fastapi import APIRouter, HTTPException
from datetime import timedelta
from app.core import auth
from app.schemas.user import LoginRequest, UserCreate
from app.services import user_service

router = APIRouter()

# 회원가입
@router.post("/api/auth/join")
def join(user: UserCreate):
    try:
        user_service.create_user(user)
        return {"message": "회원가입 성공"}
    except Exception:
        raise HTTPException(status_code=400, detail="이미 존재하는 아이디입니다.")

# 로그인
@router.post("/api/auth/login")
def login(data: LoginRequest):
    user_data = user_service.get_user(data.id)

    if not user_data:
        raise HTTPException(status_code=400, detail="사용자가 존재하지 않습니다.")

    if not user_service.verify_password(data.password, user_data["password"]):
        raise HTTPException(status_code=400, detail="비밀번호가 일치하지 않습니다.")

    access_token = auth.create_access_token(
        data={"sub": data.id},
        expires_delta=timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    if data.deviceToken:
        user_service.save_device_token(user_data["id"], data.deviceToken)

    return {
        "id": user_data["id"],
        "uid": user_data["uid"],
        "access_token": access_token,
        "token_type": "bearer",
        "userName": user_data["userName"],
        "profileImage": user_data["profileImage"]
    }