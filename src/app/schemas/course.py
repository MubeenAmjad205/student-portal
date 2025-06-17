# File: app/schemas/course.py
from pydantic import BaseModel, Field, validator, HttpUrl
from typing import List, Optional, Any
from datetime import datetime
import uuid
from ..schemas.video import VideoUpdate

class VideoCreate(BaseModel):
    youtube_url: str = Field(..., description="YouTube video URL")
    title: Optional[str] = Field(None, description="Video title")
    description: Optional[str] = Field(None, description="Video description")

    @validator('youtube_url')
    def validate_youtube_url(cls, v):
        if not v.startswith(('https://www.youtube.com/', 'https://youtu.be/')):
            raise ValueError('Invalid YouTube URL format')
        return v

class VideoRead(BaseModel):
    id: str = Field(..., description="Video ID")
    youtube_url: str = Field(..., description="YouTube video URL")
    title: Optional[str] = Field(None, description="Video title")
    description: Optional[str] = Field(None, description="Video description")

    class Config:
        orm_mode = True

class VideoWithCheckpoint(BaseModel):
    id: str = Field(..., description="Video ID")
    youtube_url: str = Field(..., description="YouTube video URL")
    title: Optional[str] = Field(None, description="Video title")
    description: Optional[str] = Field(None, description="Video description")
    watched: bool = Field(..., description="Whether the video has been watched")

    class Config:
        orm_mode = True

class CourseBase(BaseModel):
    title: str
    description: str
    price: float
    thumbnail_url: Optional[str] = None
    difficulty_level: Optional[str] = None
    outcomes: Optional[str] = ""
    prerequisites: Optional[str] = ""
    curriculum: Optional[str] = ""

class CourseCreate(CourseBase):
    pass

class CourseCreateAdmin(CourseBase):
    """Schema for creating a course by admin with additional fields"""
    preview_video: Optional[VideoCreate] = None
    videos: List[VideoCreate] = []
    created_by: Optional[str] = None
    status: str = "active"

    class Config:
        orm_mode = True

class CourseUpdate(CourseBase):
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None

class CourseRead(BaseModel):
    """Simplified course read schema with only essential fields"""
    id: uuid.UUID
    title: str
    thumbnail_url: Optional[str] = None
    expiration_date: Optional[datetime] = None

    class Config:
        orm_mode = True

class CourseListRead(CourseRead):
    total_enrollments: int = 0
    active_enrollments: int = 0
    average_progress: float = 0.0

class CourseExploreList(BaseModel):
    id: uuid.UUID
    title: str
    price: float
    thumbnail_url: Optional[str] = None

class CourseExploreDetail(CourseBase):
    id: uuid.UUID

class CourseCurriculumDetail(BaseModel):
    curriculum: str

class CourseDetail(CourseRead):
    videos: List["VideoRead"] = []

class CourseBasicDetail(BaseModel):
    id: uuid.UUID
    title: str
    thumbnail_url: Optional[str] = None

    class Config:
        orm_mode = True

class DescriptionSchema(BaseModel):
    description: str

class OutcomesSchema(BaseModel):
    outcomes: str

class PrerequisitesSchema(BaseModel):
    prerequisites: str

class CurriculumSchema(BaseModel):
    curriculum: str

class CourseProgress(BaseModel):
    completed_videos: int
    total_videos: int
    progress_percentage: float

class AdminCourseStats(BaseModel):
    """Schema for course statistics in admin panel"""
    total_enrollments: int = Field(..., description="Total number of enrollments")
    active_enrollments: int = Field(..., description="Number of active enrollments")
    completed_enrollments: int = Field(..., description="Number of completed enrollments")
    average_progress: float = Field(..., description="Average course progress percentage")
    total_revenue: float = Field(..., description="Total revenue from the course")
    last_updated: datetime = Field(..., description="Last update timestamp")

    class Config:
        orm_mode = True

class AdminCourseList(BaseModel):
    """Schema for course list in admin panel"""
    id: uuid.UUID = Field(..., description="Course ID")
    title: str = Field(..., description="Course title")
    price: float = Field(..., description="Course price")
    total_enrollments: int = Field(..., description="Total number of enrollments")
    active_enrollments: int = Field(..., description="Number of active enrollments")
    average_progress: float = Field(..., description="Average course progress")
    status: str = Field(..., description="Course status (active/inactive)")
    created_at: datetime = Field(..., description="Course creation date")
    updated_at: datetime = Field(..., description="Last update date")

    class Config:
        orm_mode = True

class AdminCourseDetail(BaseModel):
    """Schema for detailed course information in admin panel"""
    id: uuid.UUID = Field(..., description="Course ID")
    title: str = Field(..., description="Course title")
    description: str = Field(..., description="Course description")
    price: float = Field(..., description="Course price")
    thumbnail_url: Optional[str] = Field(None, description="Course thumbnail URL")
    difficulty_level: Optional[str] = Field(None, description="Course difficulty level")
    created_by: str = Field(..., description="Course creator")
    updated_by: str = Field(..., description="Last updater")
    created_at: datetime = Field(..., description="Course creation date")
    updated_at: datetime = Field(..., description="Last update date")
    status: str = Field(..., description="Course status")
    videos: List[VideoRead] = Field(..., description="Course videos")

    class Config:
        orm_mode = True
