from fastapi import APIRouter, HTTPException, Depends, Query
from app.core import auth
from app.services import user_service
from app.schemas.user import FriendInfo, QuitRequest

router = APIRouter()

# 사용자 정보 조회
@router.get("/api/users/{id}")
def get_user_info(id: str, _: str = Depends(auth.get_current_user)):
    user_data = user_service.get_user(id)
    if not user_data:
        raise HTTPException(status_code=400, detail="존재하지 않는 사용자입니다.")
    return {
        "id": id,
        "username": user_data.get("userName", ""),
        "profileImage": user_data.get("profileImage", None)
    }

# 아이디 중복 확인
@router.get("/api/users/{id}/exists")
def check_id(id: str):
    if user_service.get_user(id):
        raise HTTPException(status_code=400, detail="이미 존재하는 아이디입니다.")
    return {"message": "사용 가능한 아이디입니다."}

# ------------------ SEARCH -------------------

# 서치
@router.get("/api/users/search")
def search_users(prefix: str = Query(..., min_length=1)):
    results = user_service.search_users_by_prefix(prefix)
    return results

# ------------------ ME -------------------

# 친구(맞팔) 목록 조회
@router.get("/api/me/friends", response_model=list[FriendInfo])
def get_my_friendlist(user_id: str = Depends(auth.get_current_user)):
    return user_service.get_friendlist(user_id) or []

# 팔로잉 목록 조회
@router.get("/api/me/following", response_model=list[FriendInfo])
def get_my_followinglist(user_id: str = Depends(auth.get_current_user)):
    return user_service.get_following_list(user_id) or []

# 팔로워 목록 조회
@router.get("/api/me/followers", response_model=list[FriendInfo])
def get_my_followerlist(user_id: str = Depends(auth.get_current_user)):
    return user_service.get_follower_list(user_id) or []

# 토큰 수정
@router.put("/api/me/device-token")
def update_device_token(deviceToken: str, user_id: str = Depends(auth.get_current_user)):
    # 기기 토큰이 있으면 저장
    if deviceToken:
        user_service.save_device_token(user_id, deviceToken)

    return {"message": "저장 완료"}

# 회원 탈퇴
@router.delete("/api/me")
def quit(req: QuitRequest, user_id: str = Depends(auth.get_current_user)):
    user_data = user_service.get_user(user_id)
    if not user_data:
        raise HTTPException(status_code=400, detail="사용자를 찾을 수 없습니다.")
    if not user_service.verify_password(req.password, user_data["password"]):
        raise HTTPException(status_code=400, detail="비밀번호가 일치하지 않습니다.")
    if not user_service.delete_user(user_id):
        raise HTTPException(status_code=400, detail="회원 탈퇴에 실패했습니다.")
    return {"message": "회원 탈퇴가 완료되었습니다."}

# ------------------ ME/follow -------------------

# 팔로우 하기
@router.post("/api/follow/{target_id}")
def follow_user(target_id: str, user_id: str = Depends(auth.get_current_user)):
    result = user_service.follow_user(user_id, target_id)
    if result == "self_follow":
        raise HTTPException(status_code=400, detail="자기 자신을 팔로우할 수 없습니다.")
    if result == "not_found":
        raise HTTPException(status_code=404, detail="대상 사용자를 찾을 수 없습니다.")
    if result == "already_following":
        raise HTTPException(status_code=400, detail="이미 팔로우 중입니다.")
    return {"message": f"{target_id}님을 팔로우했습니다."}

# 팔로우 끊기
@router.delete("/api/follow/{target_id}")
def unfollow_user(target_id: str, user_id: str = Depends(auth.get_current_user)):
    result = user_service.unfollow_user(user_id, target_id)
    if result == "not_following":
        raise HTTPException(status_code=400, detail="팔로우 상태가 아닙니다.")
    return {"message": f"{target_id}님을 언팔로우했습니다."}

# ------------------ {id}/ -------------------

# 친구(맞팔) 목록 조회
@router.get("/api/{id}/friends", response_model=list[FriendInfo])
def get_friendlist(id: str, _: str = Depends(auth.get_current_user)):
    return user_service.get_friendlist(id) or []

# 팔로잉 목록 조회
@router.get("/api/{id}/following", response_model=list[FriendInfo])
def get_followinglist(id: str, _: str = Depends(auth.get_current_user)):
    return user_service.get_following_list(id) or []

# 팔로워 목록 조회
@router.get("/api/{id}/followers", response_model=list[FriendInfo])
def get_followerlist(id: str, _: str = Depends(auth.get_current_user)):
    return user_service.get_follower_list(id) or []

