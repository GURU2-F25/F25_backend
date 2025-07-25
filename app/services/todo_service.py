from datetime import datetime
from app.database import db
from app.schemas.todo import CategoryCreate, TodoCreate

def get_user_categories(user: str):
    try:
        user_ref = db.collection("users").document(user)
        category_docs = user_ref.collection("categories").stream()
        categories = []
        for doc in category_docs:
            data = doc.to_dict()
            categories.append({
                "id": doc.id,
                "name": data.get("name"),
                "color": data.get("color")
            })
        return categories
    except Exception as e:
        print(e)
        return []
    
def get_user_todos_by_date(user: str, date: str):
    try:
        user_ref = db.collection("users").document(user)
        # duedate가 date와 같은 투두만 조회
        todo_docs = user_ref.collection("todos")\
            .where("duedate", "==", date)\
            .order_by("duedate")\
            .stream()
        
        todos = []
        for doc in todo_docs:
            data = doc.to_dict()
            todos.append({
                "id": doc.id,
                "name": data.get("name"),
                "category_id": data.get("category_id"),
                "duedate": data.get("duedate"),
                "repeat": data.get("repeat")
            })
        return todos
    except Exception as e:
        print(e)
        return []
    
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