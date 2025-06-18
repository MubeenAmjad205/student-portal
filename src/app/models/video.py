# File: app/models/video.py
from sqlmodel import SQLModel, Field, Relationship
import uuid
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .course import Course

class Video(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    course_id: uuid.UUID = Field(foreign_key="course.id", nullable=False)
    youtube_url: str
    title: Optional[str] = None
    description: Optional[str] = None

    course: "Course" = Relationship(back_populates="videos", sa_relationship_kwargs={"foreign_keys": "Video.course_id"})
