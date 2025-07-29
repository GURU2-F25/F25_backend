import os
import base64
from datetime import datetime
from app.core.database import db
from passlib.context import CryptContext
from app.schemas.user import UserCreate
from google.cloud import firestore
from google.cloud.firestore_v1.field_path import FieldPath  
from app.utils.common import generate_uuid_with_timestamp
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

def get_user(user_id: str):
    """
    user_id를 기반으로 사용자 정보를 조회합니다.
    uuid 필드가 없을 경우, 자동으로 uuid + timestamp 형식으로 생성합니다.
    """
    user_ref = db.collection("users").document(user_id)
    user_doc = user_ref.get()

    if user_doc.exists:
        user_data = user_doc.to_dict()
        
        if "uid" not in user_data:
            generated_uuid = generate_uuid_with_timestamp()
            user_ref.update({"uid": generated_uuid})
            user_data["uid"] = generated_uuid  # 반환값에도 포함되게
        
        return user_data

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
    uid = generate_uuid_with_timestamp()
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")

    user_ref.set({
        "id": user.id,
        "uid":uid,
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
        follows = db.collection("follow").where("follower_id", "==", user_id).stream()
        for doc in follows:
            doc.reference.delete()

        follows = db.collection("follow").where("followee_id", "==", user_id).stream()
        for doc in follows:
            doc.reference.delete()        

        return True
    except Exception as e:
        print(f"[ERROR] 유저 삭제 실패: {e}")
        return False
    
# 팔로우 요청
def follow_user(follower_id: str, followee_id: str) -> str:
    if follower_id == followee_id:
        return "self_follow"

    user = db.collection("users").document(followee_id).get()
    if not user.exists:
        return "not_found"

    follow_ref = db.collection("follow").document(f"{follower_id}_{followee_id}")
    if follow_ref.get().exists:
        return "already_following"

    follow_ref.set({
        "follower_id": follower_id,
        "followee_id": followee_id,
        "timestamp": datetime.utcnow()
    })
    return "success"

#팔로우 끊기
def unfollow_user(follower_id: str, followee_id: str) -> str:
    follow_ref = db.collection("follow").document(f"{follower_id}_{followee_id}")
    if follow_ref.get().exists:
        follow_ref.delete()
        return "unfollowed"
    return "not_following"

# 친구 목록 조회
def get_friendlist(user_id: str) -> list[dict]:
    try:
        following = db.collection("follow").where("follower_id", "==", user_id).stream()
        result = []
        for f in following:
            data = f.to_dict()
            followee_id = data["followee_id"]
            # 맞팔 여부 확인
            if db.collection("follow").document(f"{followee_id}_{user_id}").get().exists:
                user_doc = db.collection("users").document(followee_id).get()
                if user_doc.exists:
                    user_data = user_doc.to_dict()
                    result.append({
                        "id": followee_id,
                        "userName": user_data.get("userName", ""),
                        "profileImage": user_data.get("profileImage")
                    })
        return result
    except Exception as e:
        print(f"[ERROR] 친구 목록 조회 실패: {e}")
        return []
    

# 팔로잉 목록 조회
def get_following_list(user_id: str) -> list[dict]:
    follows = db.collection("follow").where("follower_id", "==", user_id).stream()
    result = []
    for doc in follows:
        data = doc.to_dict()
        followee_doc = db.collection("users").document(data["followee_id"]).get()
        if followee_doc.exists:
            u = followee_doc.to_dict()
            result.append({
                "id": data["followee_id"],
                "userName": u.get("userName", ""),
                "profileImage": u.get("profileImage")
            })
    return result

# 팔로워 목록 조회 
def get_follower_list(user_id: str) -> list[dict]:
    try:
        followers = db.collection("follow").where("followee_id", "==", user_id).stream()
        result = []
        for f in followers:
            data = f.to_dict()
            follower_id = data["follower_id"]
            user_doc = db.collection("users").document(follower_id).get()
            if user_doc.exists:
                user_data = user_doc.to_dict()
                result.append({
                    "id": follower_id,
                    "userName": user_data.get("userName", ""),
                    "profileImage": user_data.get("profileImage")
                })
        return result
    except Exception as e:
        print(f"[ERROR] 팔로워 목록 조회 실패: {e}")
        return []

# 전체 유저 가져오기
def get_all_users_with_tokens():
    users_ref = db.collection("users")
    # deviceToken 필드가 존재하고 빈 문자열이 아닌 문서만 필터링 (Firestore에서 직접 빈 문자열 필터링은 안 될 수 있어서 필드 존재만 체크)
    query = users_ref.where("deviceToken", "!=", "").stream()

    result = []
    for doc in query:
        data = doc.to_dict()
        token = data.get("deviceToken")
        if token:  # None 또는 빈 문자열 아닌 경우만 추가
            result.append({
                "id": doc.id,
                "fcm_token": token,
                "userName": data.get("userName", ""),
                # 필요한 필드 추가 가능
            })

    return result

# 유저 검색
def search_users_by_prefix(prefix: str):
    try:
        start = prefix
        end = prefix + "\uf8ff"
        print(start)

        user_query = (
            db.collection("users")
            .order_by(FieldPath.document_id())
            .start_at([start])
            .end_at([end])
            .stream()
        )

        results = []
        for doc in user_query:
            data = doc.to_dict()

            # 민감 정보 필터링: password, token, email 등 제거
            safe_data = {
                "id": doc.id,
                "uid": data.get("uid"),
                "profileImage": data.get("profileImage"),
                "userName": data.get("nickname"),   # 예시 필드
            }

            results.append(safe_data)

        return results
    except Exception as e:
        print("Error:", e)
        return []
