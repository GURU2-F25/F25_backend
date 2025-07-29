from fastapi import APIRouter, HTTPException, Depends, Query, Body
from app.core import auth
from app.schemas.todo import TaskResponse, CategoryCreate, TodoCreate
from app.services import todo_service

router = APIRouter()

# ------------------ CATEGORY -------------------

# 내 카테고리 조회
@router.get("/api/category/me", response_model=list[CategoryCreate])
def get_my_category(user_id: str = Depends(auth.get_current_user)):
    categories = todo_service.get_user_categories(user_id)
    return categories or []

# 다른사람 카테고리 조회
@router.get("/api/category/{id}", response_model=list[CategoryCreate])
def get_my_category(id: str, _: str = Depends(auth.get_current_user)):
    categories = todo_service.get_user_categories(id)
    return categories or []

# 카테고리 생성
@router.post("/api/category")
def create_category(category: CategoryCreate = Body(...), user_id: str = Depends(auth.get_current_user)):
    result = todo_service.create_category(user_id, category)
    if result:
        return {"message": f"Category '{category.name}'를 정상적으로 생성했습니다."}
    raise HTTPException(status_code=400, detail=f"Category '{category.name}' 생성에 실패했습니다.")

# 카테고리 수정
@router.put("/api/category/{category_id}")
def update_category(
    category_id: str,
    category: CategoryCreate = Body(...),
    user_id: str = Depends(auth.get_current_user)
):
    result = todo_service.update_category(user_id, category)
    if result:
        return {"message": f"Category '{category.name}'를 정상적으로 업데이트했습니다."}
    raise HTTPException(status_code=400, detail=f"Category '{category.name}' 업데이트에 실패했습니다.")

# 카테고리 삭제
@router.delete("/api/category/{category_id}")
def delete_category(category_id: str, user_id: str = Depends(auth.get_current_user)):
    result = todo_service.delete_category(user_id, category_id)
    if result:
        return {"message": f"Category를 정상적으로 삭제했습니다."}
    raise HTTPException(status_code=400, detail="Category 삭제에 실패했습니다.")

# ------------------ TODO -------------------

# 내 투두리스트 조회
@router.get("/api/todo/me", response_model=list[TodoCreate])
def get_my_todos(date: str = Query(...), user_id: str = Depends(auth.get_current_user)):
    todos = todo_service.get_user_todos_by_date(user_id, date)
    return todos or []

# 다른 사람 투두리스트 조회
@router.get("/api/todo/{id}", response_model=list[TodoCreate])
def get_shared_todos(id: str, date: str = Query(...), _: str = Depends(auth.get_current_user)):
    todos = todo_service.get_user_todos_by_date(id, date)
    return todos or []

# 투두 생성
@router.post("/api/todo")
def create_todo(todo: TodoCreate = Body(...), user_id: str = Depends(auth.get_current_user)):
    result = todo_service.create_todo(user_id, todo)
    if result:
        return {"message": f"Todo '{todo.name}'를 정상적으로 생성했습니다."}
    raise HTTPException(status_code=400, detail=f"Todo '{todo.name}' 생성에 실패했습니다.")

# 투두 수정
@router.put("/api/todo/{todo_id}")
def update_todo(todo_id: str, todo: TodoCreate = Body(...), user_id: str = Depends(auth.get_current_user)):
    todo.id = todo_id  # ID는 URL에서 받음
    result = todo_service.update_todo(user_id, todo)
    if result:
        return {"message": f"Todo '{todo.name}'를 정상적으로 업데이트했습니다."}
    raise HTTPException(status_code=400, detail=f"Todo '{todo.name}' 업데이트에 실패했습니다.")

# 투두 삭제
@router.delete("/api/todo/{todo_id}")
def delete_todo(todo_id: str, user_id: str = Depends(auth.get_current_user)):
    result = todo_service.delete_todo(user_id, todo_id)
    if result:
        return {"message": f"Todo를 정상적으로 삭제했습니다."}
    raise HTTPException(status_code=400, detail="Todo 삭제에 실패했습니다.")

# 투두 체크/해제
@router.patch("/api/todo/{todo_id}/check")
def check_todo(todo_id: str, user_id: str = Depends(auth.get_current_user)):
    result = todo_service.check_todo(user_id, todo_id)
    if result:
        return {"message": "Todo를 정상적으로 업데이트했습니다."}
    raise HTTPException(status_code=400, detail="Todo 업데이트에 실패했습니다.")