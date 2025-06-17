# File: application/src/app/models/course.py
from sqlmodel import SQLModel, Field, Relationship
import uuid
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import Column, Text, ForeignKey
import json
from datetime import datetime

if TYPE_CHECKING:
    from .video import Video
    from .enrollment import Enrollment
    from .course_progress import CourseProgress
    from .assignment import Assignment
    from .quiz import Quiz

class Course(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    title: str
    description: str
    price: float = Field(default=0.0)
    thumbnail_url: Optional[str] = None
    preview_video_id: Optional[uuid.UUID] = Field(
        default=None, sa_column=Column(ForeignKey("video.id", ondelete="SET NULL"))
    )
    videos: List["Video"] = Relationship(back_populates="course", sa_relationship_kwargs={"foreign_keys": "Video.course_id", "cascade": "all, delete-orphan"})
    enrollments: List["Enrollment"] = Relationship(back_populates="course", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    progress: List["CourseProgress"] = Relationship(back_populates="course", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    assignments: List["Assignment"] = Relationship(back_populates="course", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    quizzes: List["Quiz"] = Relationship(back_populates="course", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    difficulty_level: Optional[str] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    outcomes: str = Field(default="", sa_column=Column(Text))
    prerequisites: str = Field(default="", sa_column=Column(Text))
    curriculum: str = Field(default="", sa_column=Column(Text))
    status: str = Field(default="active")
