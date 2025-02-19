from sqlmodel import Field, SQLModel
from typing import Optional
from datetime import datetime, timezone

class InsertChat(SQLModel):
    sender_id: int
    receiver_id: int
    message: Optional[str] = None
    uuid: str
    image: Optional[str] = None
    created_at: str

class ChatResponse(SQLModel):
    id: int
    sender_id: int
    receiver_id: int
    message: Optional[str] = None
    uuid: str
    image: Optional[str] = None
    status: str = "sent"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc))

class Model(SQLModel, table=True):
    __tablename__ = "chats"
    id: Optional[int] = Field(default=None, primary_key=True)
    sender_id: int
    receiver_id: int
    message: Optional[str] = None
    uuid: str = Field(sa_column_kwargs={"unique": True})
    image: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc))