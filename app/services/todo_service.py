from datetime import datetime
from app.core.database import db
from app.schemas.todo import CategoryCreate, TodoCreate
from app.utils.common import generate_uuid_with_timestamp

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
        # date 문자열 -> datetime.date 변환 (예: "2025-07-28")
        target_date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
        target_weekday = target_date.weekday()  # 월=0, 화=1, ..., 일=6

        todo_docs = user_ref.collection("todos")\
            .where("duedate", "<=", date)\
            .order_by("duedate")\
            .stream()

        todos = []
        for doc in todo_docs:
            data = doc.to_dict()
            repeat = data.get("repeat")
            duedate_str = data.get("duedate")
            if not duedate_str:
                continue

            # duedate도 date형으로 변환
            duedate = datetime.datetime.strptime(duedate_str, "%Y-%m-%d").date()

            # 필터링 조건:
            # 1) duedate == target_date
            # 2) repeat == "daily"
            # 3) repeat == "weekly" and 요일 일치
            if duedate == target_date:
                pass
            elif repeat == "daily":
                pass
            elif repeat == "weekly" and duedate.weekday() == target_weekday:
                pass
            else:
                continue

            todos.append({
                "id": doc.id,
                "name": data.get("name"),
                "category_id": data.get("category_id"),
                "duedate": duedate_str,
                "repeat": repeat,
                "checked": data.get("checked")
            })
        return todos
    except Exception as e:
        print(e)
        return []

    
def create_category(user: str, category: CategoryCreate):
    try:
        user_ref = db.collection("users").document(user)
        category.id = generate_uuid_with_timestamp() 
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
        todo.id = generate_uuid_with_timestamp()  
        user_ref.collection("todos").document(todo.id).set({
            "name": todo.name,
            "category_id": todo.category_id,
            "duedate": todo.duedate,
            "repeat": todo.repeat,
            "checked": todo.checked
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
                "repeat": todo.repeat,
                "checked": todo.checked
            })
            return True
        else:
            return False
    except Exception as e:
        print(e)
        return False

def check_todo(user: str, todo_id: str):
    try:
        user_ref = db.collection("users").document(user)
        todo_ref = user_ref.collection("todos").document(todo_id)
        doc = todo_ref.get()

        if doc.exists:
            data = doc.to_dict()
            current_checked = data.get("checked", "false")  # 기본값 "false"
            
            print(f"현재 checked 값: {current_checked}")  # 디버깅용
            
            # 만약 checked가 문자열이면
            if isinstance(current_checked, str):
                new_checked = "true" if current_checked == "false" else "false"
            else:
                # 혹시 boolean일 경우에도 대비
                new_checked = not current_checked

            todo_ref.update({"checked": new_checked})
            return True
        else:
            print("해당 문서가 존재하지 않습니다.")
            return False
    except Exception as e:
        print(f"에러 발생: {e}")
        return False
    
def get_unchecked_todos_due_today(user_id: str):
    try:
        today_str = datetime.now().date().isoformat()
        target_date = datetime.strptime(today_str, "%Y-%m-%d").date()
        target_weekday = target_date.weekday()  # 0=월요일, 6=일요일

        user_ref = db.collection("users").document(user_id)
        todo_docs = user_ref.collection("todos")\
            .where("duedate", "<=", today_str)\
            .order_by("duedate")\
            .stream()

        todos = []
        for doc in todo_docs:
            data = doc.to_dict()
            repeat = data.get("repeat")
            duedate_str = data.get("duedate")
            checked = data.get("checked")

            if checked != "false":
                continue
            if not duedate_str:
                continue

            duedate = datetime.strptime(duedate_str, "%Y-%m-%d").date()

            # repeat 조건 필터링
            if duedate == target_date:
                pass
            elif repeat == "daily":
                pass
            elif repeat == "weekly" and duedate.weekday() == target_weekday:
                pass
            else:
                continue

            todos.append({
                "id": doc.id,
                "name": data.get("name"),
                "category_id": data.get("category_id"),
                "duedate": duedate_str,
                "repeat": repeat,
                "checked": checked,
            })

        return todos
    except Exception as e:
        print(f"Error in get_unchecked_todos_due_today: {e}")
        return []