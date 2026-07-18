"""This file contains the Pydantic models (schemas) for authentication-related data structures."""


import uuid

from pydantic import BaseModel, EmailStr
from app.models.user import UserRole

class SignupRequest(BaseModel):
    """Schema for user signup request."""
    name: str
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    """Schema for user login request."""
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: EmailStr
    role: UserRole

    class Config:
        from_attributes = True # This allows Pydantic to read data from ORM models directly