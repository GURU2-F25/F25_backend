# app/jobs/reminder.py
from app.core.database import messaging
from app.services import todo_service, user_service

def send_due_soon_notifications():
    users = user_service.get_all_users_with_tokens()
    for user in users:
        todos = todo_service.get_unchecked_todos_due_today(user["id"])
        if todos:
            message = messaging.Message(
                token=user["fcm_token"],
                notification=messaging.Notification(
                    title="아직 안 끝낸 일이 있어요!",
                    body=f"오늘 마감인데 아직 완료 안 된 할일이 {len(todos)}개 있어요!",
                ),
            )
            response = messaging.send(message)
            print(f"✅ Sent to {user['id']} - {response}")
