# File: app/schemas/notification.py
from pydantic import BaseModel
from datetime import datetime
import uuid

class NotificationRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    event_type: str
    details: str
    timestamp: datetime

    class Config:
        orm_mode = True
