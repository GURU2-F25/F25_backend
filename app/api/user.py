
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from app.core import auth
from app.schemas.user import UserCreate, RequestId
from datetime import timedelta
from app.services import user_service


router = APIRouter()


@router.post("/api/user/join")
def join(user: UserCreate):
    try:
        result = user_service.create_user(user)
        return {"message": "회원가입 성공"}
    except Exception as e:
        raise HTTPException(status_code=400, detail="이미 존재하는 아이디입니다.")

@router.post("/api/user/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user_data = user_service.get_user(form_data.username)

    if not user_data:
        raise HTTPException(status_code=400, detail="사용자가 존재하지 않습니다.")

    if not user_service.verify_password(form_data.password, user_data["password"]):
        raise HTTPException(status_code=400, detail="비밀번호가 일치하지 않습니다.")


    access_token = auth.create_access_token(
        data={"sub": form_data.username},
        expires_delta=timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "userName": user_data["userName"],
        "profileImage": user_data["profileImage"]
    }
    
@router.post("/api/user/check-id")
def check_id(req: RequestId):
    id_check = user_service.get_user(req.id)
    if not id_check:
        return {
            "message":"사용 가능한 아이디입니다."
        }
    if id_check:
        raise HTTPException(status_code = 422, detail = "이미 존재하는 아이디입니다.")
