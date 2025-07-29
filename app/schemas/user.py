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

class LoginRequest(BaseModel):
    id: str
    password: str
    deviceToken: Optional[str] = None
class RequestId(BaseModel):
    id: str

class QuitRequest(BaseModel):
    password: str

class FriendInfo(BaseModel):
    id: str
    userName: str
    profileImage: Optional[str] = None
    
class UserSearchResult(BaseModel):
    id: str
    uid: Optional[str] = None
    profileImage: Optional[str] = None
    userName: Optional[str] = None
    followers: list[str]
    following: list[str]