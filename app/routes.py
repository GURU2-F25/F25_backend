from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from google.cloud.firestore_v1 import Client
from app.database import db
from app.models import User
from typing import List, Optional
import uuid