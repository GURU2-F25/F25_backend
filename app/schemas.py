from pydantic import BaseModel
from typing import Optional

'''
@descrption users의 구조

users (collection)
 └── hello123 (document)
     ├── password: $2b$12$....
     └── profileImage: "images/hello.png"
'''
class UserCreate(BaseModel):
    id: str
    password: str
    userName: str
    profileImage: str

class RequestId(BaseModel):
    id: str