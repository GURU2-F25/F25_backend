from fastapi import APIRouter, HTTPException, Depends
from datetime import timedelta
from app.core import auth
from app.schemas.user import LoginRequest, UserCreate, FriendInfo, QuitRequest
from app.services import user_service

router = APIRouter()

# 1. 회원가입
@router.post("/api/users")
def join(user: UserCreate):
    try:
        user_service.create_user(user)
        return {"message": "회원가입 성공"}
    except Exception:
        raise HTTPException(status_code=400, detail="이미 존재하는 아이디입니다.")

# 2. 로그인
@router.post("/api/user/login")
def login(data: LoginRequest):
    user_data = user_service.get_user(data.username)

    if not user_data:
        raise HTTPException(status_code=400, detail="사용자가 존재하지 않습니다.")

    if not user_service.verify_password(data.password, user_data["password"]):
        raise HTTPException(status_code=400, detail="비밀번호가 일치하지 않습니다.")

    access_token = auth.create_access_token(
        data={"sub": data.username},
        expires_delta=timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    # 기기 토큰이 있으면 저장
    if data.deviceToken:
        user_service.save_device_token(user_data["id"], data.deviceToken)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "userName": user_data["userName"],
        "profileImage": user_data["profileImage"]
    }
# 3. 아이디 중복 확인
@router.get("/api/users/exists")
def check_id(id: str):
    if user_service.get_user(id):
        raise HTTPException(status_code=400, detail="이미 존재하는 아이디입니다.")
    return {"message": "사용 가능한 아이디입니다."}

# 4. 회원 탈퇴
@router.delete("/api/users/me")
def quit(req: QuitRequest, user_id: str = Depends(auth.get_current_user)):
    user_data = user_service.get_user(user_id)
    if not user_data:
        raise HTTPException(status_code=400, detail="사용자를 찾을 수 없습니다.")
    if not user_service.verify_password(req.password, user_data["password"]):
        raise HTTPException(status_code=400, detail="비밀번호가 일치하지 않습니다.")
    if not user_service.delete_user(user_id):
        raise HTTPException(status_code=400, detail="회원 탈퇴에 실패했습니다.")
    return {"message": "회원 탈퇴가 완료되었습니다."}

# 5. 사용자 정보 조회
@router.get("/api/users/{id}")
def get_user_info(id: str, user_id: str = Depends(auth.get_current_user)):
    user_data = user_service.get_user(id)
    if not user_data:
        raise HTTPException(status_code=400, detail="존재하지 않는 사용자입니다.")
    return {
        "id": id,
        "username": user_data.get("userName", ""),
        "profileImage": user_data.get("profileImage", None)
    }

# ------------------ ME -------------------

# 6. 친구 목록 조회
@router.get("/api/me/friends", response_model=list[FriendInfo])
def get_friendlist(user_id: str = Depends(auth.get_current_user)):
    return user_service.get_friendlist(user_id) or []

# 7. 토큰 수정
@router.put("/api/me/device-token")
def login(deviceToken: str, user_id: str = Depends(auth.get_current_user)):
    # 기기 토큰이 있으면 저장
    if deviceToken:
        user_service.save_device_token(user_id, deviceToken)

    return {"message": "저장 완료"}

# ------------------ ME/FRIENDS-REQUESTS -------------------

# 8. 팔로우 하기
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



# 9. 팔로우 끊기
@router.delete("/api/follow/{target_id}")
def unfollow_user(target_id: str, user_id: str = Depends(auth.get_current_user)):
    result = user_service.unfollow_user(user_id, target_id)
    if result == "not_following":
        raise HTTPException(status_code=400, detail="팔로우 상태가 아닙니다.")
    return {"message": f"{target_id}님을 언팔로우했습니다."}

# 10. 팔로워 목록 조회
@router.get("/api/me/followers", response_model=list[FriendInfo])
def get_followerlist(user_id: str = Depends(auth.get_current_user)):
    return user_service.get_follower_list(user_id) or []