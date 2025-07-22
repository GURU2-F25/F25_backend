from pydantic import BaseModel
from typing import Optional

class User(BaseModel):
    uid: str
    username: str
    email: str