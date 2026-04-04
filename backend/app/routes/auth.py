"""
Authentication Routes
Endpoints for user authentication and minimal hackathon flows.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from passlib.context import CryptContext
from datetime import datetime

try:
    from app.database import users_collection
except ImportError:
    users_collection = None

from app.models.user_model import UserCreate, UserLogin, AuthResponse
from app.utils.auth import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

# Configure passlib to use bcrypt exclusively
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def signup(request: UserCreate):
    if users_collection is None:
        raise HTTPException(status_code=503, detail="Database connection not configured")
        
    existing_user = users_collection.find_one({"email": request.email.lower()})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email is already registered")
        
    hashed_password = get_password_hash(request.password)
    
    user_dict = {
        "email": request.email.lower(),
        "hashed_password": hashed_password,
        "created_at": datetime.utcnow()
    }
    
    result = users_collection.insert_one(user_dict)

    access_token = create_access_token(str(result.inserted_id), request.email.lower())
    return {
        "message": "User created successfully",
        "userId": str(result.inserted_id),
        "accessToken": access_token,
        "tokenType": "bearer"
    }

@router.post("/login", response_model=AuthResponse)
async def login(request: UserLogin):
    if users_collection is None:
        raise HTTPException(status_code=503, detail="Database connection not configured")
        
    user = users_collection.find_one({"email": request.email.lower()})
    
    # Generic failure condition prevents account enumeration side-channels
    if not user or not verify_password(request.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
        
    access_token = create_access_token(str(user["_id"]), user["email"])
    return {
        "message": "Login successful",
        "userId": str(user["_id"]),
        "accessToken": access_token,
        "tokenType": "bearer"
    }
