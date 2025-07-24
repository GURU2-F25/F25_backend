from datetime import datetime
from app.database import db
from app.schemas.user import UserCreate
from app.schemas.todo import CategoryCreate, TodoCreate

def create_category(user: str, category: CategoryCreate):
    try:
        user_ref = db.collection("users").document(user)
        user_ref.collection("categories").document(category.id).set({
            "name": category.name,
            "color": category.color
        })
        return True
    except Exception as e:
        print(e)
        return False
    
def create_todo(user: str, todo: TodoCreate):
    user_ref = db.collection("users").document(user)
    user_ref.collection("todos").document(todo.id).set({
        "name": todo.name,
        "category": todo.category,
        "duedate": todo.date,
        "repeat": todo.repeat
    })
    
def delete_category(user: str, category: str):
    user_ref = db.collection("users").document(user)
    category_ref = user_ref.collection("categories").document(category)
    doc = category_ref.get()
    if doc.exists:
        category_ref.delete()
        return True
    else:
        return False