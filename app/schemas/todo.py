from pydantic import BaseModel
from typing import Optional
from datetime import date
from typing import Literal

class CategoryCreate(BaseModel):
    id: str
    name: str
    color: str
    
class TodoCreate(BaseModel):
    id: str
    name: str
    category_id: str
    duedate: str 
    repeat: Optional[Literal["none", "daily", "weekly"]] = "none"
    checked: Optional[Literal["false", "true"]] = "false"