from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime

'''
@descrption users의 구조

users (collection)
 └── hello123 (document)
     ├── password: $2b$12$....
     └── profileImage: Base64 or null
'''
class UserCreate(BaseModel):
    id: str
    password: str
    userName: str
    profileImage: Optional[str] = None

class RequestId(BaseModel):
    id: str

class FriendRequestInfo(BaseModel):
    from_id: str
    to_id: str
    status: Literal["spending", "accepted", "rejected"]
    timestamp: datetime

class FriendRequest(BaseModel):
    to_id: str

class FriendInfo(BaseModel):
    id: str
    userName: str
    profileImage: Optional[str] = None