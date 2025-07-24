from fastapi import APIRouter, Header, HTTPException, Depends,  Query
import uuid
from app.core import  auth
from app.schemas.todo import CategoryCreate, TodoCreate
from datetime import timedelta
from app.services import todo_service


router = APIRouter()

@router.get("/api/create-category")
def create_category(category_name: str = Query(..., alias="name"), 
                    category_color: str = Query(..., alias="color"), 
                    user_id: str = Depends(auth.get_current_user)):
    if not (category_name&category_color):
        raise HTTPException(status_code=400, detail="Missing category name")

    category_id = str(uuid.uuid4())
     # Pydantic 객체 생성
    category = CategoryCreate(
        id=category_id,
        name=category_name,
        color=category_color
    )
    result = todo_service.create_category(user_id, category)

    if result:
        return {"message": f"Category '{category_name}'를 정상적으로 생성했습니다."}
    else :
        return {"message": f"Category '{category_name}' 생성에 실패했습니다."}