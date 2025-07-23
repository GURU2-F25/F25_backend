import os
import base64
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from app.schemas import UserCreate, RequestId
from datetime import timedelta
from app import crud, auth
from datetime import datetime
from dotenv import load_dotenv

router = APIRouter()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

@router.post("/user/join")
def join(user: UserCreate):
    SAVE_DIR = os.environ["PROFILE_IMAGES_DIR_PATH"]
    os.makedirs(SAVE_DIR, exist_ok=True)
    
    if not user.profileImage or user.profileImage=="":
        pass
    elif "," in user.profileImage:
        header, base64_data = user.profileImage.split(",", 1)
    else:
        base64_data = user.profileImage
    try:
        # 확장자 추출 (기본값: png)
        ext = "png"
        if "image/jpeg" in user.profileImage:
            ext = "jpg"
        elif "image/webp" in user.profileImage:
            ext = "webp"

        # 디코딩
        image_data = base64.b64decode(base64_data)

        # 저장 경로 생성
        filename = f"{user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{ext}"
        filepath = os.path.join(SAVE_DIR, filename)
        filepath = filepath.replace("\\", "/")
        user.profileImage = filepath

        # 파일 저장
        with open(filepath, "wb") as f:
            f.write(image_data)
            
    except Exception as e:
        print("에러 발생:", e)
        user.profileImage = ""
        
    
        
    created = crud.create_user(user.id, user.password, user.userName, user.profileImage)
    if not created:
        raise HTTPException(status_code=400, detail="이미 존재하는 사용자 ID입니다.")
    return {"message": "회원가입 성공"}

@router.post("/user/login")
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
@router.post("/user/check-id")
def check_id(req: RequestId):
    id_check = crud.get_user(req.id)
    if not id_check:
        return {
            "message":"사용 가능한 아이디입니다."
        }
    if id_check:
        raise HTTPException(status_code = 422, detail = "이미 존재하는 아이디입니다.")
