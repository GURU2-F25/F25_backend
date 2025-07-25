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
    status: Literal["pending", "accepted", "rejected"]
    timestamp: datetime
    from_userName: Optional[str] = None
    from_profileImage: Optional[str] = None

class FriendRequest(BaseModel):
    from_id: str
    to_id: str

class FriendInfo(BaseModel):
    id: str
    userName: str
    profileImage: Optional[str] = None