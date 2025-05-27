# File: application/src/app/models/quiz_audit_log.py
from sqlmodel import SQLModel, Field
import uuid
from datetime import datetime
from typing import Optional

class QuizAuditLog(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    student_id: uuid.UUID = Field(foreign_key="user.id")
    quiz_id: uuid.UUID = Field(foreign_key="quiz.id")
    action: str  # e.g., "submit", "view_result"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    details: Optional[str] = None
