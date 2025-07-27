import os
import base64
from datetime import datetime
from app.core.database import db
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
    hashed_pw = pwd_context.hash(user.password)

    user_ref.set({
        "id": user.id,
        "password": hashed_pw, 
        "userName": user.userName,
        "profileImage": user.profileImage
    })

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def save_device_token(user_id: str, token: str):
    user_ref = db.collection("users").document(user_id)
    user_doc = user_ref.get()

    if user_doc.exists:
        user_ref.update({"deviceToken": token})
    else:
        # 유저가 없다면 새로 생성할 수도 있음 (선택)
        user_ref.set({"deviceToken": token})

def delete_user(user_id: str)->bool:
    try:
        db.collection("users").document(user_id).delete()
        friends = db.collection("friends").where("user_id", "==", user_id).stream()
        for doc in friends:
            doc.reference.delete()

        friends = db.collection("friends").where("friend_id", "==", user_id).stream()
        for doc in friends:
            doc.reference.delete()
        requests = db.collection("friend_requests").where("from_id", "==", user_id).stream()
        for doc in requests:
            doc.reference.delete()

        requests = db.collection("friend_requests").where("to_id", "==", user_id).stream()
        for doc in requests:
            doc.reference.delete()

        return True
    except Exception as e:
        print(f"[ERROR] 유저 삭제 실패: {e}")
        return False

def send_FriendRequest(from_id: str, to_id: str) -> str:
    if from_id == to_id:
        return "self_request"
    
    to_user = db.collection("users").document(to_id).get()
    if not to_user.exists:
        return "not_found"
    
    friend_doc = db.collection("friends").document(f"{from_id}_{to_id}").get()
    if friend_doc.exists:
        return "already_friend"

    req_doc = db.collection("friend_requests").document(f"{from_id}_{to_id}").get()
    if req_doc.exists:
        return "already_requested"

    db.collection("friend_requests").document(f"{from_id}_{to_id}").set({
        "from_id": from_id,
        "to_id": to_id,
        "status": "pending",
        "timestamp": datetime.utcnow()
    })
    return "success"

def get_friendlist(user_id: str) -> list[dict]:
    try:
        friends = db.collection("friends").where("user_id", "==", user_id).stream()
        result = []

        for doc in friends:
            data = doc.to_dict()
            friend_id = data["friend_id"]
            user_doc = db.collection("users").document(friend_id).get()
            if user_doc.exists:
                user_data = user_doc.to_dict()
                result.append({
                    "id": friend_id,
                    "userName": user_data.get("userName", ""),
                    "profileImage": user_data.get("profileImage")
                })
        return result
    except Exception as e:
        print(f"[ERROR] 친구 목록 조회 실패: {e}")
        return []
    
def respond_friendRequest(from_id: str, to_id: str, accept: bool) -> str:
    request_ref = db.collection("friend_requests").document(f"{from_id}_{to_id}")
    request_doc = request_ref.get()

    if not request_doc.exists:
        return "not_found"

    status = "accepted" if accept else "rejected"
    request_ref.update({"status": status})

    if accept:
            db.collection("friends").document(f"{from_id}_{to_id}").set({
                "user_id": from_id,
                "friend_id": to_id,
                "timestamp": datetime.utcnow()
            })
            db.collection("friends").document(f"{to_id}_{from_id}").set({
                "user_id": to_id,
                "friend_id": from_id,
                "timestamp": datetime.utcnow()
            })
    else:
        request_ref.delete()

    return status

def get_friendRequests(to_id: str) -> list[dict]:
    try:
        requests = db.collection("friend_requests") \
            .where("to_id", "==", to_id) \
            .where("status", "==", "pending") \
            .stream()

        result = []
        for doc in requests:
            data = doc.to_dict()
            from_user_doc = db.collection("users").document(data["from_id"]).get()
            if from_user_doc.exists:
                from_user = from_user_doc.to_dict()
                result.append({
                    "from_id": data["from_id"],
                    "to_id": data["to_id"],
                    "status": data["status"],
                    "timestamp": data["timestamp"],
                    "from_userName": from_user.get("userName", ""),
                    "from_profileImage": from_user.get("profileImage", None)
                })

        return result
    except Exception as e:
        print(f"[ERROR] 친구 요청 목록 조회 실패: {e}")
        return []