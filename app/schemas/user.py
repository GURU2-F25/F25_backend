from pydantic import BaseModel
from typing import Optional

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