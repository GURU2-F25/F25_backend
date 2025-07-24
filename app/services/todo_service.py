from datetime import datetime
from app.database import db
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
    try:
        user_ref = db.collection("users").document(user)
        user_ref.collection("todos").document(todo.id).set({
            "name": todo.name,
            "category_id": todo.category_id,
            "duedate": todo.duedate,
            "repeat": todo.repeat
        })
        return True
    except Exception as e:
        print(e)
        return False
    
def delete_category(user: str, category: str):
    user_ref = db.collection("users").document(user)
    category_ref = user_ref.collection("categories").document(category)
    doc = category_ref.get()
    if doc.exists:
        category_ref.delete()
        return True
    else:
        return False
    
def delete_todo(user: str, todo: str):
    user_ref = db.collection("users").document(user)
    todo_ref = user_ref.collection("todos").document(todo)
    doc = todo_ref.get()
    if doc.exists:
        todo_ref.delete()
        return True
    else:
        return False

def update_category(user: str, category: CategoryCreate):
    try:
        user_ref = db.collection("users").document(user)
        category_ref = user_ref.collection("categories").document(category.id)
        doc = category_ref.get()
        if doc.exists:
            category_ref.update({
                "name": category.name,
                "color": category.color
            })
            return True
        else:
            return False
    except Exception as e:
        print(e)
        return False

def update_todo(user: str, todo: TodoCreate):
    try:
        user_ref = db.collection("users").document(user)
        todo_ref = user_ref.collection("todos").document(todo.id)
        doc = todo_ref.get()
        if doc.exists:
            todo_ref.update({
                "name": todo.name,
                "category_id": todo.category_id,
                "duedate": todo.duedate,
                "repeat": todo.repeat
            })
            return True
        else:
            return False
    except Exception as e:
        print(e)
        return False