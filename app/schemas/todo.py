from pydantic import BaseModel
from typing import Optional
from datetime import date
from typing import Literal

class CategoryCreate:
    id: str
    name: str
    color: str
    
class TodoCreate:
    id: str
    name: str
    category: str
    duedate: date 
    repeat: Optional[Literal["none", "daily", "weekly"]] = "none"