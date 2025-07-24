from fastapi import APIRouter, Header, HTTPException, Depends
from typing import Optional
import firebase_admin
from firebase_admin import credentials, firestore, auth
from app.schemas.todo import CategoryCreate, TodoCreate
from datetime import timedelta
from app.services import user_service


router = APIRouter()

def get_current_user(authorization: Optional[str] = Header(None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header missing or invalid")

    token = authorization.split(" ")[1]
    try:
        decoded_token = auth.verify_id_token(token)
        user_id = decoded_token["uid"]
        return user_id
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.get("/api/create-category")
def create_category(category: str, user_id: str = Depends(get_current_user)):
    if not category:
        raise HTTPException(status_code=400, detail="Missing category name")

    # category_ref = db.collection("users").document(user_id).collection("categories").document(category)
    # category_ref.set({"name": category})

    # return {"message": f"Category '{category}' created successfully"}