from sqlmodel import SQLModel, Field
from typing import Optional
import uuid
from sqlalchemy import Column, String, Boolean, UUID

class VideoProgress(SQLModel, table=True):
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    video_id: uuid.UUID = Field(foreign_key="video.id", nullable=False)
    completed: bool = Field(default=False)
