from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from app.schemas import UserCreate, RequestId
from datetime import timedelta
from app import crud, auth

router = APIRouter()

@router.post("/api/join")
def join(user: UserCreate):
    created = crud.create_user(user.id, user.password, user.userName, user.profileImage)
    if not created:
        raise HTTPException(status_code=400, detail="이미 존재하는 사용자 ID입니다.")
    return {"message": "회원가입 성공"}

@router.post("/api/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user_data = crud.get_user(form_data.username)
    if not user_data:
        raise HTTPException(status_code=400, detail="사용자가 존재하지 않습니다.")

    if not crud.verify_password(form_data.password, user_data["password"]):
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
@router.post("/api/check-id")
def check_id(req: RequestId):
    id_check = crud.get_user(req.id)
    if not id_check:
        return {
            "message":"사용 가능한 아이디입니다."
        }
    if id_check:
        raise HTTPException(status_code = 422, detail = "이미 존재하는 아이디입니다.")
