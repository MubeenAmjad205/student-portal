from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING
import uuid
from sqlalchemy import Column, String, Boolean, UUID

if TYPE_CHECKING:
    from .video import Video
    from .user import User

class VideoProgress(SQLModel, table=True):
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    video_id: uuid.UUID = Field(foreign_key="video.id", nullable=False)
    completed: bool = Field(default=False)

    video: "Video" = Relationship(back_populates="progress")
    user: "User" = Relationship(back_populates="video_progress")
