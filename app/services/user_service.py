import os
import base64
from datetime import datetime
from app.core.database import db
from passlib.context import CryptContext
from app.schemas.user import UserCreate
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
        
         # followers: 그 사용자를 팔로우하는 사람들
        follower_docs = db.collection("follow").where("followee_id", "==", user_id).stream()
        followers = [doc.to_dict().get("follower_id") for doc in follower_docs]

        # following: 그 사용자가 팔로우하는 사람들
        following_docs = db.collection("follow").where("follower_id", "==", user_id).stream()
        following = [doc.to_dict().get("followee_id") for doc in following_docs]
        
        if "uid" not in user_data:
            generated_uuid = generate_uuid_with_timestamp()
            user_ref.update({"uid": generated_uuid})
            user_data["uid"] = generated_uuid  # 반환값에도 포함되게
        
        user_data["followers"]=followers
        user_data["following"]=following
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
    회원 탈퇴 처리. 사용자 계정, 팔로우 관계 등을 모두 삭제합니다.
    """
    try:
        db.collection("users").document(user_id).delete()
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
    """
    사용자가 다른 사용자를 팔로우합니다.
    - 본인을 팔로우할 수 없습니다.
    - 존재하지 않는 사용자를 팔로우할 수 없습니다.
    - 이미 팔로우 중인 경우 중복 팔로우를 방지합니다.
    - 팔로우 관계를 생성합니다.
    """
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
    """
    사용자가 다른 사용자의 팔로우를 취소합니다.
    - 팔로우 관계가 존재하는 경우 삭제합니다.
    - 팔로우 관계가 존재하지 않으면 아무 작업도 하지 않습니다.
    """
    follow_ref = db.collection("follow").document(f"{follower_id}_{followee_id}")
    if follow_ref.get().exists:
        follow_ref.delete()
        return "unfollowed"
    return "not_following"

# 팔로잉 목록 조회
def get_following_list(user_id: str) -> list[dict]:
    """
    주어진 사용자(user_id)가 팔로우하고 있는 사용자 목록을 조회합니다.

    - follow 컬렉션에서 follower_id가 user_id인 문서를 조회합니다.
    - 각 followee_id에 해당하는 사용자 정보를 users 컬렉션에서 가져옵니다.
    - userName과 profileImage 등 기본 프로필 정보를 함께 반환합니다.
    """
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
    """
    주어진 사용자(user_id)를 팔로우하고 있는 사용자 목록을 조회합니다.
    - follow 컬렉션에서 followee_id가 user_id인 문서를 조회합니다.
    - 각 follower_id에 해당하는 사용자 정보를 users 컬렉션에서 가져옵니다.
    - userName과 profileImage 등 기본 프로필 정보를 함께 반환합니다.
    - Firestore 조회 중 오류가 발생하면 에러 메시지를 출력하고 빈 리스트 반환
    """
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
    """
    FCM 푸시 알림을 위한 사용자 목록을 가져옵니다.
    - deviceToken 필드가 존재하고 빈 문자열이 아닌 사용자만 조회합니다.
      (deviceToken은 로그인을 1회 이상 한 사용자에게만 생성됩니다.)
    - Firestore의 where 조건으로 빈 문자열 비교는 제한이 있으므로
      'deviceToken' 필드가 존재하면서 None/빈 문자열이 아닌 경우만 필터링합니다.
    """
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
            })

    return result

# 유저 검색
def search_users_by_prefix(prefix: str):
    """
    주어진 접두사(prefix)를 기반으로 사용자 ID를 검색합니다.
    - 사용자 문서 ID 기준으로 검색합니다 (document_id 사용).
    - 최대 5명의 사용자만 검색됩니다.
    - 각 사용자에 대해 기본 정보(id, uid, profileImage, userName)를 포함합니다.
    - 각 사용자에 대해 followers(자신을 팔로우하는 사람들) 및 following(자신이 팔로우하는 사람들) 목록도 함께 반환합니다.
    """
    try:
        start = prefix
        end = prefix + "\uf8ff"

        # 먼저 유저 검색
        user_query = (
            db.collection("users")
            .order_by(FieldPath.document_id())
            .start_at([start])
            .end_at([end])
            .limit(5)
            .stream()
        )

        # 검색된 유저 ID들 수집
        users = []
        user_ids = []
        for doc in user_query:
            data = doc.to_dict()
            target_user_id = doc.id

            users.append({
                "id": target_user_id,
                "uid": data.get("uid"),
                "profileImage": data.get("profileImage"),
                "userName": data.get("userName"),
            })
            user_ids.append(target_user_id)

        # isFollowing 추가
        for user in users:
            target_id = user["id"]

            # followers: 그 사용자를 팔로우하는 사람들
            follower_docs = db.collection("follow").where("followee_id", "==", target_id).stream()
            followers = [doc.to_dict().get("follower_id") for doc in follower_docs]

            # following: 그 사용자가 팔로우하는 사람들
            following_docs = db.collection("follow").where("follower_id", "==", target_id).stream()
            following = [doc.to_dict().get("followee_id") for doc in following_docs]

            user["followers"] = followers
            user["following"] = following
        return users

    except Exception as e:
        print("Error:", e)
        return []
