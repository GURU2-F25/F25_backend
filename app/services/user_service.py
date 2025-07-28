import os
import base64
from datetime import datetime
from app.core.database import db
from passlib.context import CryptContext
from app.schemas.user import UserCreate
from dotenv import load_dotenv
# 비밀번호 해싱 설정
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# 프로필 이미지 저장 함수
def save_profile_image(user: UserCreate) -> str:
    """
    사용자로부터 받은 base64 인코딩 이미지 데이터를 저장하고,
    저장된 이미지 경로를 반환합니다.
    """
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    load_dotenv(os.path.join(BASE_DIR, ".env"))
    profile_dir = os.environ["PROFILE_IMAGES_DIR_PATH"]
    SAVE_DIR = os.path.join(BASE_DIR, profile_dir)
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
    
# 사용자 정보 조회
def get_user(user_id: str):
    """
    user_id를 기반으로 사용자 정보를 조회합니다.
    """
    user_ref = db.collection("users").document(user_id)
    user_doc = user_ref.get()
    if user_doc.exists:
        return user_doc.to_dict()
    return None

# 사용자 생성 (회원가입)
def create_user(user: UserCreate):
    """
    신규 사용자 등록. 아이디 중복 여부를 확인하고,
    비밀번호는 해시 처리되며, 프로필 이미지는 저장됩니다.
    """
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

# 비밀번호 검증
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    사용자가 입력한 비밀번호와 DB에 저장된 해시값을 비교합니다.
    """
    return pwd_context.verify(plain_password, hashed_password)


# 디바이스 토큰 저장 (선택적 기능)
def save_device_token(user_id: str, token: str):
    """
    유저의 디바이스 토큰을 저장합니다.
    """
    user_ref = db.collection("users").document(user_id)
    user_doc = user_ref.get()

    if user_doc.exists:
        user_ref.update({"deviceToken": token})
    else:
        # 유저가 없다면 새로 생성할 수도 있음 (선택)
        user_ref.set({"deviceToken": token})

# 사용자 및 관련 데이터 삭제
def delete_user(user_id: str)->bool:
    """
    회원 탈퇴 처리. 사용자 계정, 친구 관계, 친구 요청 등을 모두 삭제합니다.
    """
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
    
# 친구 요청 보내기
def send_FriendRequest(from_id: str, to_id: str) -> str:
    """
    친구 요청 전송 로직. 중복 요청, 자기 자신 요청, 이미 친구 여부 등을 검사합니다.
    """
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

# 친구 목록 조회
def get_friendlist(user_id: str) -> list[dict]:
    """
    사용자 ID 기준으로 친구 목록을 반환합니다.
    """
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
    
# 친구 요청 수락 또는 거절
def respond_friendRequest(from_id: str, to_id: str, accept: bool) -> str:
    """
    친구 요청 수락 또는 거절 처리.
    수락 시 양방향 친구 관계를 생성합니다.
    """
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
        # 거절 시 요청 삭제
        request_ref.delete()

    return status

# 받은 친구 요청 목록 조회
def get_friendRequests(to_id: str) -> list[dict]:
    """
    사용자가 받은 친구 요청 목록을 반환합니다.
    """
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