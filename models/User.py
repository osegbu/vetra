from sqlmodel import Field, SQLModel
from typing import Optional, List
from datetime import datetime, timezone

class CreateUser(SQLModel):
    user_name: str
    hashed_password: str = Field(..., min_length=6)

class Auth(SQLModel):
    id: int
    user_name: str
    profile_image: Optional[str] = None

class UserResponse(SQLModel):
    id: int
    user_name: str
    profile_image: str
    status: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    chats: Optional[List] = None

class Model(SQLModel, table=True):
    __tablename__ = "users"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_name: str = Field(index=True, unique=True)
    hashed_password: str = Field(..., min_length=6) 
    profile_image: Optional[str] = None 
    status: str = Field(default="Offline")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
