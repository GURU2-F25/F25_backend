from app.database import db
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_user(user_id: str):
    user_ref = db.collection("users").document(user_id)
    user_doc = user_ref.get()
    if user_doc.exists:
        return user_doc.to_dict()
    return None

def create_user(user_id: str, password: str, userName: str, profileImage: str):
    user_ref = db.collection("users").document(user_id)
    if user_ref.get().exists:
        return None  # 이미 존재

    hashed_password = pwd_context.hash(password)
    user_ref.set({
        "password": hashed_password,
        "userName": userName,
        "profileImage": profileImage,
    })
    return True

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

