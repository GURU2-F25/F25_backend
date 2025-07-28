from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from app.core import auth
from app.schemas.user import LoginRequest, UserCreate, FriendInfo, FriendRequest, FriendRequestInfo, ReceivedFriendRequest, QuitRequest
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

# ------------------ ME/FRIENDS-REQUESTS -------------------

# 7. 친구 요청 보내기
@router.post("/api/me/friend-requests")
def send_friend_request(req: FriendRequest, user_id: str = Depends(auth.get_current_user)):
    result = user_service.send_FriendRequest(user_id, req.to_id)
    if result == "self_request":
        raise HTTPException(status_code=400, detail="자기 자신에게는 친구 요청을 보낼 수 없습니다.")
    if result == "not_found":
        raise HTTPException(status_code=400, detail="존재하지 않는 사용자입니다.")
    if result == "already_friend":
        raise HTTPException(status_code=400, detail="이미 친구입니다.")
    if result == "already_requested":
        raise HTTPException(status_code=400, detail="이미 친구 요청을 보냈습니다.")
    return {"message": f"{req.to_id}에게 친구 요청을 보냈습니다."}

# 8. 친구 요청 수락
@router.put("/api/me/friend-requests/{from_id}")
def accept_friend_request(from_id: str, user_id: str = Depends(auth.get_current_user)):
    result = user_service.respond_friendRequest(from_id, user_id, accept=True)
    if result == "not_found":
        raise HTTPException(status_code=400, detail="친구 요청이 존재하지 않습니다.")
    return {"message": "친구 요청을 수락했습니다."}

# 9. 친구 요청 거절
@router.delete("/api/me/friend-requests/{from_id}")
def reject_friend_request(from_id: str, user_id: str = Depends(auth.get_current_user)):
    result = user_service.respond_friendRequest(from_id, user_id, accept=False)
    if result == "not_found":
        raise HTTPException(status_code=400, detail="친구 요청이 존재하지 않습니다.")
    return {"message": "친구 요청을 거절했습니다."}

# 10. 받은 친구 요청 목록
@router.get("/api/me/friend-requests", response_model=list[FriendRequestInfo])
def get_friend_requests(user_id: str = Depends(auth.get_current_user)):
    return user_service.get_friendRequests(user_id)
