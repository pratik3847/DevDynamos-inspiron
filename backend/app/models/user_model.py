"""
User DB Model & Pydantic Schema
Defines the data structure for users.
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """Base user model with common fields."""
    email: str


class UserCreate(BaseModel):
    """Model for user registration."""
    email: str
    password: str


class UserLogin(BaseModel):
    """Model for user login."""
    email: str
    password: str


class UserInDB(BaseModel):
    """User model as stored in database."""
    email: str
    hashed_password: str
    created_at: Optional[datetime] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "hashed_password": "$2b$12$...",
                "created_at": "2024-01-01T00:00:00"
            }
        }


class UserResponse(BaseModel):
    """Model for user data in responses (no password)."""
    userId: str
    email: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "userId": "507f1f77bcf86cd799439011",
                "email": "user@example.com"
            }
        }


class AuthResponse(BaseModel):
    """Response after successful authentication."""
    message: str
    userId: str
    accessToken: str
    tokenType: str = "bearer"
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Login successful",
                "userId": "507f1f77bcf86cd799439011",
                "accessToken": "<jwt>",
                "tokenType": "bearer"
            }
        }
