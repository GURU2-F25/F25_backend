from fastapi import APIRouter, HTTPException, Body
from app.jobs import reminder
from firebase_admin import messaging

router = APIRouter()

# push
@router.post("/api/push/test")
def send_test_push(token: str = Body(...), title: str = Body(...), body: str = Body(...)):
    try:
        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            token=token,
        )
        response = messaging.send(message)
        return {"result": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# push - git action으로 주기적 실행
@router.post("/api/push/reminder")
def push_reminder():
    reminder.send_due_soon_notifications()
    return {"result": "notifications sent"}