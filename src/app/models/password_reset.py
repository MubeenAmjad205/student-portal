# File: application/src/app/models/password_reset.py
from sqlmodel import SQLModel, Field
import uuid
from datetime import datetime, timedelta

class PasswordReset(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False, index=True)
    pin: str = Field(nullable=False, description="6-digit reset PIN")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(
        default_factory=lambda: datetime.utcnow() + timedelta(minutes=15)
    )
    used: bool = Field(default=False)
