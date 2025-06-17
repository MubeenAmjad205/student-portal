# assignment.py
from sqlmodel import SQLModel, Field, Relationship
import uuid
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .course import Course
    from .user import User

class Assignment(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    course_id: uuid.UUID = Field(foreign_key="course.id")
    title: str
    description: str
    due_date: datetime

    submissions: List["AssignmentSubmission"] = Relationship(back_populates="assignment", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    course: "Course" = Relationship(back_populates="assignments")

class AssignmentSubmission(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    assignment_id: uuid.UUID = Field(foreign_key="assignment.id")
    student_id: uuid.UUID = Field(foreign_key="user.id")
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    content_url: str

    # ← New fields:
    grade: Optional[float] = Field(default=None, nullable=True)
    feedback: Optional[str] = Field(default=None, nullable=True)
    student: "User" = Relationship(back_populates="assignment_submissions")
    assignment: "Assignment" = Relationship(back_populates="submissions")
