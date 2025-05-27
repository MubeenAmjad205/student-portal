# File: application/src/app/models/course.py
from sqlmodel import SQLModel, Field, Relationship
import uuid
from typing import List, Optional
from sqlalchemy import Column, Text
import json
from datetime import datetime

class Course(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    title: str
    description: str
    price: float = Field(default=0.0)
    thumbnail_url: Optional[str] = None
    preview_video_id: Optional[uuid.UUID] = Field(default=None, foreign_key="video.id")
    videos: List["Video"] = Relationship(back_populates="course", sa_relationship_kwargs={"foreign_keys": "Video.course_id"})
    enrollments: List["Enrollment"] = Relationship(back_populates="course")
    difficulty_level: Optional[str] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    outcomes: str = Field(default="", sa_column=Column(Text))
    prerequisites: str = Field(default="", sa_column=Column(Text))
    curriculum: str = Field(default="", sa_column=Column(Text))
    status: str = Field(default="active")
