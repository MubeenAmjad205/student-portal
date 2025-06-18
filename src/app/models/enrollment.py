# File: app/models/enrollment.py
from sqlmodel import SQLModel, Field, Relationship, JSON
import uuid
from datetime import datetime, timedelta
from typing import Optional, TYPE_CHECKING
import pytz
from app.utils.time import get_pakistan_time

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.course import Course

import uuid

class Enrollment(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: str = Field(foreign_key="user.id")
    course_id: str = Field(foreign_key="course.id")
    status: str = Field(default="pending")  # pending, approved, rejected
    enroll_date: Optional[datetime] = None
    expiration_date: Optional[datetime] = None
    is_accessible: bool = Field(default=False)
    days_remaining: Optional[int] = None
    audit_log: list = Field(sa_type=JSON, default_factory=list)
    last_access_date: Optional[datetime] = None

    user: "User" = Relationship(back_populates="enrollments")
    course: "Course" = Relationship(back_populates="enrollments")

    def update_expiration_status(self):
        """Update the expiration status and days remaining"""
        current_time = get_pakistan_time()
        
        if self.expiration_date:
            # Convert both dates to UTC for comparison
            expiration_utc = self.expiration_date.replace(tzinfo=None)
            current_utc = current_time.replace(tzinfo=None)
            
            # Calculate days remaining
            self.days_remaining = (expiration_utc - current_utc).days
            
            # Update is_accessible based on expiration
            self.is_accessible = self.days_remaining > 0
        else:
            self.days_remaining = None
            self.is_accessible = True
        self.last_access_date = current_time
