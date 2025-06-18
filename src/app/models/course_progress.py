from sqlmodel import SQLModel, Field
from typing import Optional
import uuid
from sqlalchemy import Column, Boolean, Float

class CourseProgress(SQLModel, table=True):
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    course_id: uuid.UUID = Field(foreign_key="course.id", nullable=False)
    completed: bool = Field(default=False)
    progress_percentage: float = Field(default=0.0)
    last_accessed_video_id: Optional[uuid.UUID] = Field(foreign_key="video.id", nullable=True)
    completed_at: Optional[str] = None  