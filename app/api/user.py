
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from app.core import auth
from app.schemas.user import UserCreate, RequestId, FriendInfo, FriendRequest, FriendRequestInfo, ReceivedFriendRequest, QuitRequest
from datetime import timedelta
from app.services import user_service


router = APIRouter()


@router.post("/api/user/join")
def join(user: UserCreate):
    try:
        result = user_service.create_user(user)
        return {"message": "회원가입 성공"}
    except Exception as e:
        raise HTTPException(status_code=400, detail="이미 존재하는 아이디입니다.")

@router.post("/api/user/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user_data = user_service.get_user(form_data.username)

    if not user_data:
        raise HTTPException(status_code=400, detail="사용자가 존재하지 않습니다.")

    if not user_service.verify_password(form_data.password, user_data["password"]):
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
    
@router.post("/api/user/check-id")
def check_id(req: RequestId):
    id_check = user_service.get_user(req.id)
    if not id_check:
        return {
            "message":"사용 가능한 아이디입니다."
        }
    if id_check:
        raise HTTPException(status_code = 422, detail = "이미 존재하는 아이디입니다.")
    
@router.post("/api/user/quit")
def quit(req: QuitRequest, user_id: str = Depends(auth.get_current_user)):
    user_data = user_service.get_user(user_id)
    
    if not user_data:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    if not user_service.verify_password(req.password, user_data["password"]):
        raise HTTPException(status_code=400, detail="비밀번호가 일치하지 않습니다.")

    result = user_service.delete_user(user_id)
    if not result:
        raise HTTPException(status_code=500, detail="회원 탈퇴에 실패했습니다.")

    return {"message": "회원 탈퇴가 완료되었습니다."}


@router.get("/api/user/find-id")
def id_find(id: str, user_id: str = Depends(auth.get_current_user)):
    user_data = user_service.get_user(id)
    if not user_data:
        raise HTTPException(detail = "존재하지 않는 사용자입니다.")
    return{
        "id" : id,
        "username": user_data.get("userName", ""),
        "profileImage": user_data.get("profileImage", None)
    }

@router.get("/api/user/get-friendlist", response_model=list[FriendInfo])
def get_friendlist(user_id: str = Depends(auth.get_current_user)):
    friends = user_service.get_friendlist(user_id)

    if not friends:
        return []  
    
    return friends

@router.post("/api/user/send-friendrequest")
def send_FriendRequest(req: FriendRequest, user_id: str = Depends(auth.get_current_user)):
    result = user_service.send_FriendRequest(user_id, req.to_id)

    if result == "self_request":
        raise HTTPException(detail="자기 자신에게는 친구 요청을 보낼 수 없습니다.")
    elif result == "not_found":
        raise HTTPException(detail="존재하지 않는 사용자입니다.")
    elif result == "already_friend":
        raise HTTPException(detail="이미 친구입니다.")
    elif result == "already_requested":
        raise HTTPException(detail="이미 친구 요청을 보냈습니다.")
    
    return {"message": f"{req.to_id}에게 친구 요청을 보냈습니다."}

@router.post("/api/user/accept-friend")
def accept_friend_request(req: ReceivedFriendRequest, user_id: str = Depends(auth.get_current_user)):
    result = user_service.respond_friendRequest(req.from_id, user_id, accept=True)

    if result == "not_found":
        raise HTTPException(detail="친구 요청이 존재하지 않습니다.")
    return {"message": "친구 요청을 수락했습니다."}

@router.get("/api/user/get-friendrequests", response_model=list[FriendRequestInfo])
def get_friendRequests(user_id: str = Depends(auth.get_current_user)):
    requests = user_service.get_friendRequests(user_id)
    return requests

@router.post("/api/user/reject-friend")
def reject_friend_request(req: ReceivedFriendRequest, user_id: str = Depends(auth.get_current_user)):
    result = user_service.respond_friendRequest(req.from_id, user_id, accept=False)

    if result == "not_found":
        raise HTTPException(detail="친구 요청이 존재하지 않습니다.")
    return {"message": "친구 요청을 거절했습니다."}