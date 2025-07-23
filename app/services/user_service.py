import os
import base64
from datetime import datetime
from app.database import db
from passlib.context import CryptContext
from app.schemas.user import UserCreate
from dotenv import load_dotenv

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def save_profile_image(user: UserCreate) -> str:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    load_dotenv(os.path.join(BASE_DIR, ".env"))
    SAVE_DIR = os.environ["PROFILE_IMAGES_DIR_PATH"]
    os.makedirs(SAVE_DIR, exist_ok=True)
    
    profile_data = user.profileImage
    if not profile_data:
        return ""

    try:
        if "," in profile_data:
            _, base64_data = profile_data.split(",", 1)
        else:
            base64_data = profile_data

        ext = "png"
        if "image/jpeg" in profile_data:
            ext = "jpg"
        elif "image/webp" in profile_data:
            ext = "webp"

        image_data = base64.b64decode(base64_data)
        filename = f"{user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{ext}"
        filepath = os.path.join(SAVE_DIR, filename).replace("\\", "/")

        with open(filepath, "wb") as f:
            f.write(image_data)

        return filepath
    except Exception as e:
        print("이미지 저장 실패:", e)
        return ""

def get_user(user_id: str):
    user_ref = db.collection("users").document(user_id)
    user_doc = user_ref.get()
    if user_doc.exists:
        return user_doc.to_dict()
    return None

def create_user(user: UserCreate):
    user_ref = db.collection("users").document(user.id)
    if user_ref.get().exists:
        raise ValueError("이미 존재하는 사용자 ID입니다.")

    user.profileImage = save_profile_image(user)

    user_ref.set({
        "id": user.id,
        "password": user.password,  # 실서비스라면 해시 필수!
        "userName": user.userName,
        "profileImage": user.profileImage
    })

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

