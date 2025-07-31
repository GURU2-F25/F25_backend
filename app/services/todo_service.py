from datetime import datetime
from app.core.database import db
from app.schemas.todo import CategoryCreate, CategoryUpdate, TodoCreate, TodoUpdate
from app.utils.common import generate_uuid_with_timestamp

def get_user_categories(user: str):
    """
    주어진 사용자(user)의 카테고리 목록을 조회합니다.
    처리 과정:
    - Firestore에서 해당 사용자의 문서를 참조합니다.
    - 그 하위 컬렉션인 'categories' 컬렉션을 조회하여 모든 문서를 가져옵니다.
    - 각 카테고리 문서에서 id, name, color 정보를 추출하여 리스트로 구성합니다.
    - 사용자의 카테고리 목록 리스트 (각 항목은 dict 형식으로 id, name, color 포함) 반환
    - 예외 발생 시 빈 리스트 반환
    """
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
    """
    주어진 날짜(date)에 해당하는 사용자의 할 일(todo) 목록을 조회합니다.
    처리 과정:
    - 입력된 날짜 문자열("YYYY-MM-DD")을 datetime.date로 변환합니다.
    - 사용자의 todos 서브컬렉션에서 duedate가 해당 날짜 이전 또는 같은 항목을 조회합니다.
    - 다음 조건 중 하나라도 만족하는 항목만 필터링하여 포함합니다:
        1) duedate가 정확히 target_date와 일치
        2) repeat이 "daily" (매일 반복)
        3) repeat이 "weekly"이고, 요일이 target_date와 일치
    - 조건을 만족하는 todo 리스트 (각 항목은 id, name, category_id, duedate, repeat, checked 포함) 반환
    - 예외 발생 시 빈 리스트 반환
    """
    try:
        user_ref = db.collection("users").document(user)
        # date 문자열 -> datetime.date 변환 (예: "2025-07-28")
        target_date = datetime.strptime(date, "%Y-%m-%d").date()
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
            duedate = datetime.strptime(duedate_str, "%Y-%m-%d").date()

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
    """
    사용자(user)의 카테고리를 생성합니다.
    - category.id를 UUID + 타임스탬프로 생성하여 고유 ID로 설정합니다.
    - Firestore의 'users/{user}/categories/{category.id}' 문서로 저장합니다.
    - 성공 시 True, 실패 시 False 반환
    """
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
    """
    사용자(user)의 할 일(todo)을 생성합니다.
    - todo.id를 UUID + 타임스탬프로 생성하여 고유 ID로 설정합니다.
    - Firestore의 'users/{user}/todos/{todo.id}' 문서로 저장합니다.
    - 성공 시 True, 실패 시 False 반환
    """
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
    """
    사용자(user)의 특정 카테고리(category)를 삭제합니다.
    - 해당 카테고리 문서가 존재할 경우 삭제 후 True 반환
    - 없으면 False 반환
    - 삭제 대상 카테고리와 연관된 모든 할 일(todo)들도 함께 삭제합니다.
    """
    user_ref = db.collection("users").document(user)
    category_ref = user_ref.collection("categories").document(category)
    doc = category_ref.get()
    if doc.exists:
        # 카테고리 삭제
        category_ref.delete()
        
        # 해당 category_id를 가진 todo 삭제
        todos_ref = user_ref.collection("todos").where("category_id", "==", category).stream()
        for todo_doc in todos_ref:
            todo_doc.reference.delete()
        
        return True
    else:
        return False
    
def delete_todo(user: str, todo: str):
    """
    사용자(user)의 특정 할 일(todo)을 삭제합니다.
    - 해당 할 일 문서가 존재하면 삭제 후 True 반환
    - 없으면 False 반환
    """
    user_ref = db.collection("users").document(user)
    todo_ref = user_ref.collection("todos").document(todo)
    doc = todo_ref.get()
    if doc.exists:
        todo_ref.delete()
        return True
    else:
        return False

def update_category(user: str, category_id: str, category: CategoryUpdate):
    """
    사용자(user)의 특정 카테고리(category_id)를 업데이트합니다.
    - 문서가 존재하면 name, color 필드를 갱신하고 True 반환
    - 문서가 없으면 False 반환
    - 예외 발생 시 False 반환
    """
    try:
        user_ref = db.collection("users").document(user)
        category_ref = user_ref.collection("categories").document(category_id)
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

def update_todo(user: str, todo_id: str, todo: TodoUpdate):
    """
    사용자(user)의 특정 할 일(todo_id)을 업데이트합니다.
    - 문서가 존재하면 주요 필드들을 갱신하고 True 반환
    - 문서가 없으면 False 반환
    - 예외 발생 시 False 반환
    """
    try:
        user_ref = db.collection("users").document(user)
        todo_ref = user_ref.collection("todos").document(todo_id)
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
    """
    특정 사용자의 할 일(todo)의 checked 상태를 토글합니다.
    - 주어진 사용자 ID(user)와 할 일 ID(todo_id)를 기반으로 문서를 조회합니다.
    - 문서가 존재할 경우, checked 값을 반전시켜 업데이트합니다.
        - 문자열 "false" → "true", "true" → "false"
        - 불리언 타입도 고려하여 True/False 반전
    - 존재하지 않으면 False 반환
    - 예외 발생 시 False 반환
    """
    try:
        user_ref = db.collection("users").document(user)
        todo_ref = user_ref.collection("todos").document(todo_id)
        doc = todo_ref.get()

        if doc.exists:
            data = doc.to_dict()
            current_checked = data.get("checked", "false")  # 기본값 "false"
            
            print(f"현재 checked 값: {current_checked}")  # 디버깅용
            
            # checked가 문자열일 경우
            if isinstance(current_checked, str):
                new_checked = "true" if current_checked == "false" else "false"
            else:
                # boolean일 경우
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
    """
    오늘 날짜 기준으로 체크되지 않은 할 일 목록을 조회합니다.    
    조건:
    - duedate가 오늘 날짜 이전 또는 오늘인 항목
    - checked 필드가 "false"인 항목 (문자열 기준)
    - 반복 조건(repeat)에 따라 오늘 수행 대상인지 판단:
        - 반복 없음: duedate가 오늘과 같을 경우만 포함
        - daily: 매일 반복되므로 포함
        - weekly: duedate의 요일과 오늘의 요일이 같을 경우 포함
    - 체크되지 않은 오늘 할 일 리스트 (각 항목은 dict 형식) 반환
    - 오류 발생 시 빈 리스트 반환
    """
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