# File: app/main.py
# File location: src/app/main.py
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import routers
from app.routers import (
    auth_router,
    profile_router,
    course_router, 
    enrollment_router,
)
from app.utils.dependencies import get_current_admin_user
from app.routers.admin_router import router as admin_router
from app.routers.student_assignment_router import router as sa_router
from app.routers.student_quiz_router import router as sq_router
from app.routers.student_dashboard_router import router as student_dashboard_router

# Import database setup
from app.db.session import create_db_and_tables

# Import Cloudinary configuration
import cloudinary
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure Cloudinary
cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET'),
    secure=True
)

# Read CORS_ORIGINS from environment, default to localhost for development
cors_origins_str = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8000")
cors_origins = [origin.strip() for origin in cors_origins_str.split(",")]

app = FastAPI(
    title="EduTech API",
    description="API for EduTech platform",
    version="1.0.0",
    allow_origins=cors_origins,  # Use origins from environment variable
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600  # Cache preflight requests for 1 hour
)

# Create database tables on startup
@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# Include routers
app.include_router(auth_router.router)
app.include_router(profile_router.router, prefix="/api/profile", tags=["Profile"])
app.include_router(course_router.router, prefix="/api/courses", tags=["Courses"])
app.include_router(enrollment_router.router, prefix="/api/enrollments", tags=["Enrollments"])
app.include_router(admin_router)
app.include_router(sa_router)
app.include_router(sq_router)
app.include_router(student_dashboard_router)
@app.get("/")
async def root():
    return {
        "message": "Welcome to EduTech API",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    } 