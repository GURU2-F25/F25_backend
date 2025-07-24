from fastapi import APIRouter, Header, HTTPException, Depends,  Query
import uuid
from app.core import  auth
from app.schemas.todo import CategoryCreate, TodoCreate
from app.services import todo_service
from datetime import datetime

router = APIRouter()

@router.get("/api/create-category")
def create_category(category_name: str = Query(..., alias="name"), 
                    category_color: str = Query(..., alias="color"), 
                    user_id: str = Depends(auth.get_current_user)):
    
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
    
    

@router.get("/api/delete_category")
def delete_category(category_id: str = Query(..., alias="category_id"), 
                    user_id: str = Depends(auth.get_current_user)):
    
     # Pydantic 객체 생성
    result = todo_service.delete_category(user_id, category_id)

    if result:
        return {"message": f"Category를 정상적으로 삭제했습니다."}
    else :
        return {"message": f"Category 삭제에 실패했습니다."}
    
@router.get("/api/update-category")
def update_category(category_id: str = Query(..., alias="category_id"),
                    category_name: str = Query(..., alias="name"), 
                    category_color: str = Query(..., alias="color"), 
                    user_id: str = Depends(auth.get_current_user)):
    
     # Pydantic 객체 생성
    category = CategoryCreate(
        id=category_id,
        name=category_name,
        color=category_color
    )
    
    result = todo_service.update_category(user_id, category)

    if result:
        return {"message": f"Category '{category_name}'를 정상적으로 업데이트했습니다."}
    else :
        return {"message": f"Category '{category_name}' 업데이트에 실패했습니다."}
    
@router.get("/api/create-todo")
def create_todo(name: str = Query(..., alias="name"), 
                category_id: str = Query(..., alias="category_id"), 
                duedate: str = Query(..., alias="duedate"), 
                repeat: str = Query(..., alias="repeat"), 
                user_id: str = Depends(auth.get_current_user)):
    
    todo_id = str(uuid.uuid4())
    print(datetime.strptime(duedate, "%Y-%m-%d").date().isoformat())
     # Pydantic 객체 생성
    todo = TodoCreate(
        id=todo_id,
        name=name,
        category_id=category_id,
        duedate=datetime.strptime(duedate, "%Y-%m-%d").date().isoformat(),
        repeat=repeat
    )
    
    result = todo_service.create_todo(user_id, todo)

    if result:
        return {"message": f"Todo '{name}'를 정상적으로 생성했습니다."}
    else :
        return {"message": f"Todo '{name}' 생성에 실패했습니다."}
    
@router.get("/api/delete_todo")
def delete_todo(todo_id: str = Query(..., alias="todo_id"), 
                user_id: str = Depends(auth.get_current_user)):
    
     # Pydantic 객체 생성
    result = todo_service.delete_todo(user_id, todo_id)

    if result:
        return {"message": f"Todo를 정상적으로 삭제했습니다."}
    else :
        return {"message": f"Todo 삭제에 실패했습니다."}