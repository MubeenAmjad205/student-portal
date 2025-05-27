# File: app/controllers/admin_controller.py

from fastapi import APIRouter, Depends, HTTPException, status, Body, Query, File, UploadFile
from sqlmodel import Session, select, func
from typing import List, Optional
from app.models.user import User
from app.models.course import Course
from app.models.video import Video
from app.models.enrollment import Enrollment
from app.models.notification import Notification
from app.models.video_progress import VideoProgress
from app.models.course_progress import CourseProgress
from app.db.session import get_db
from app.utils.dependencies import get_current_admin_user
from uuid import UUID
from sqlalchemy.orm import selectinload
from app.schemas.user import UserRead
from app.schemas.course import (
    AdminCourseList, AdminCourseDetail, AdminCourseStats,
    CourseCreate, CourseUpdate, CourseRead, CourseCreateAdmin
)
from app.schemas.video import VideoUpdate, VideoRead
from app.schemas.notification import NotificationRead
import uuid
from datetime import datetime, timedelta
from app.utils.time import get_pakistan_time
from app.models.assignment import Assignment, AssignmentSubmission
from app.models.quiz import Quiz, Question, Option
from typing import List
from fastapi import Form
from app.utils.file import save_upload_and_get_url
from app.schemas.assignment import AssignmentCreate, AssignmentRead, AssignmentList, SubmissionRead, SubmissionGrade, SubmissionStudent, SubmissionStudentsResponse
from app.schemas.quiz import QuizCreate, QuizRead

router = APIRouter(prefix="/admin", tags=["Admin"])

# 1. Enrollment Management
@router.get("/users", response_model=List[UserRead])
def list_students(session: Session = Depends(get_db), admin=Depends(get_current_admin_user)):
    query = select(User).where(User.role == "student")
    return session.exec(query).all()

from app.models.course import Course
from app.schemas.course import AdminCourseList
from sqlmodel import select

@router.get("/courses", response_model=list[AdminCourseList])
def admin_list_courses(db: Session = Depends(get_db), admin=Depends(get_current_admin_user)):
    courses = db.exec(select(Course)).all()
    # You can add more logic to calculate enrollments, progress, etc. if needed
    return [
        AdminCourseList(
            id=c.id,
            title=c.title,
            price=c.price,
            total_enrollments=0,  # Replace with actual logic if needed
            active_enrollments=0, # Replace with actual logic if needed
            average_progress=0.0, # Replace with actual logic if needed
            status=c.status,
            created_at=c.created_at,
            updated_at=c.updated_at
        ) for c in courses
    ]

# 1b. Create a new course with preview video and videos
@router.post("/courses")
async def create_course(
    course: str = Form(...),  # JSON string for the entire course data
    thumbnail: UploadFile = File(None),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    """
    Create a new course (Admin only).

    **Endpoint:** `/admin/courses` (POST)

    **Description:**
    Allows an admin to create a new course, including uploading a thumbnail and specifying a list of videos. Accepts multipart/form-data with a JSON string for the course data and an optional thumbnail image.

    **Request Body:**
    - `course` (str, required): JSON string representing the course data. Should include fields such as:
        - `title`: Course title (str, required)
        - `description`: Course description (str, required)
        - `price`: Course price (float, required)
        - `difficulty_level`: Difficulty level (str, optional)
        - `outcomes`: Outcomes (str, optional)
        - `prerequisites`: Prerequisites (str, optional)
        - `curriculum`: Curriculum (str, optional)
        - `videos`: List of video objects, each with:
            - `youtube_url` (str, required)
            - `title` (str, optional)
            - `description` (str, optional)
    - `thumbnail` (file, optional): Image file for the course thumbnail.

    **Example Request (Swagger UI):**
    - `course`: `{ "title": "Python Basics", "description": "Learn Python.", "price": 20.0, "videos": [{ "youtube_url": "https://youtu.be/example1", "title": "Intro" }] }`
    - `thumbnail`: (select a file)

    **Success Response:**
    - `200 OK` with JSON body:
    ```json
    {
      "success": true,
      "course_id": "<uuid>",
      "message": "Course created successfully"
    }
    ```

    **Errors:**
    - Returns a clear error message if the JSON is invalid or required fields are missing.
    """
    import json
    from app.models.course import Course
    from app.models.video import Video
    from datetime import datetime

    # Parse course JSON
    try:
        course_data = json.loads(course)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid course JSON")

    # Validate required fields
    title = course_data.get("title", "")
    description = course_data.get("description", "")
    price = course_data.get("price", 0)
    videos_data = course_data.get("videos", [])
    difficulty_level = course_data.get("difficulty_level")
    outcomes = course_data.get("outcomes", "")
    prerequisites = course_data.get("prerequisites", "")
    curriculum = course_data.get("curriculum", "")
    status = course_data.get("status", "active")

    if not title or len(title.strip()) < 3:
        raise HTTPException(status_code=400, detail="Course title must be at least 3 characters long")
    if not description or len(description.strip()) < 10:
        raise HTTPException(status_code=400, detail="Course description must be at least 10 characters long")
    if price < 0:
        raise HTTPException(status_code=400, detail="Course price cannot be negative")
    if not isinstance(videos_data, list):
        raise HTTPException(status_code=400, detail="Videos must be a list")

    # Check if course with same title already exists
    existing_course = db.exec(select(Course).where(Course.title == title)).first()
    if existing_course:
        raise HTTPException(status_code=400, detail="A course with this title already exists")

    # Save thumbnail if provided
    thumbnail_url = None
    if thumbnail is not None:
        thumbnail_url = save_upload_and_get_url(thumbnail, folder="thumbnails")

    # Create course object
    new_course = Course(
        title=title,
        description=description,
        price=price,
        difficulty_level=difficulty_level,
        outcomes=outcomes,
        prerequisites=prerequisites,
        curriculum=curriculum,
        status=status,
        thumbnail_url=thumbnail_url,
        created_by=admin.email,
        updated_by=admin.email,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(new_course)
    db.commit()
    db.refresh(new_course)

    # Add videos
    for video in videos_data:
        db.add(Video(
            youtube_url=video["youtube_url"],
            title=video.get("title", ""),
            description=video.get("description", ""),
            course_id=new_course.id
        ))
    db.commit()

    # Get the complete course details
    return {"success": True, "course_id": str(new_course.id), "message": "Course created successfully"}

# 2. Notifications
@router.get("/notifications", response_model=List[NotificationRead])
def get_notifications(session: Session = Depends(get_db), admin=Depends(get_current_admin_user)):
    notifications = session.exec(select(Notification).order_by(Notification.timestamp.desc()).limit(50)).all()
    return notifications

# 3. Course Management
@router.put("/courses/{course_id}", response_model=AdminCourseDetail)
async def update_course(
    course_id: str,
    course_update: CourseUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    """Update an existing course with comprehensive validation"""
    try:
        # Validate course_id format
        try:
            course_uuid = uuid.UUID(course_id)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid course ID format"
            )

        # Get existing course
        course = db.exec(
            select(Course).where(Course.id == course_uuid)
        ).first()
        
        if not course:
            raise HTTPException(
                status_code=404,
                detail="Course not found"
            )

        # Validate update data
        update_data = course_update.dict(exclude_unset=True)
        
        if "title" in update_data:
            if not update_data["title"] or len(update_data["title"].strip()) < 3:
                raise HTTPException(
                    status_code=400,
                    detail="Course title must be at least 3 characters long"
                )
            # Check for duplicate title
            existing_course = db.exec(
                select(Course)
                .where(
                    Course.title == update_data["title"],
                    Course.id != course_uuid
                )
            ).first()
            if existing_course:
                raise HTTPException(
                    status_code=400,
                    detail="A course with this title already exists"
                )

        if "description" in update_data and len(update_data["description"].strip()) < 10:
            raise HTTPException(
                status_code=400,
                detail="Course description must be at least 10 characters long"
            )

        if "price" in update_data and update_data["price"] < 0:
            raise HTTPException(
                status_code=400,
                detail="Course price cannot be negative"
            )

        # Update course fields
        for key, value in update_data.items():
            setattr(course, key, value)
            
        course.updated_by = admin.email
        course.updated_at = datetime.utcnow()
        
        try:
            db.add(course)
            db.commit()
            db.refresh(course)
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Error updating course in database: {str(e)}"
            )
        
        return await get_course_detail(course_id, db, admin)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error updating course: {str(e)}"
        )

@router.delete("/courses/{course_id}")
async def delete_course(
    course_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    """Delete a course (soft delete)"""
    try:
        course = db.exec(
            select(Course).where(Course.id == course_id)
        ).first()
        
        if not course:
            raise HTTPException(
                status_code=404,
                detail="Course not found"
            )
            
        course.status = "deleted"
        course.updated_by = admin.email
        course.updated_at = datetime.utcnow()
        
        db.add(course)
        db.commit()
        
        return {"message": "Course deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting course: {str(e)}"
        )

@router.get("/dashboard/stats", response_model=dict)
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    """Get overall platform statistics for admin dashboard"""
    try:
        # Get total courses
        total_courses = db.exec(select(func.count(Course.id))).first()
        
        # Get total enrollments
        total_enrollments = db.exec(select(func.count(Enrollment.id))).first()
        
        # Get active enrollments (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        active_enrollments = db.exec(
            select(func.count(Enrollment.id))
            .where(
                Enrollment.status == "approved",
                Enrollment.is_accessible == True
            )
        ).first()
        
        # Get total revenue
        total_revenue = db.exec(
            select(func.sum(Course.price))
            .join(Enrollment)
            .where(Enrollment.status == "approved")
        ).first() or 0
        
        # Get completion rate
        completed_courses = db.exec(
            select(func.count(CourseProgress.id))
            .where(CourseProgress.completed == True)
        ).first()
        
        completion_rate = (completed_courses / total_enrollments * 100) if total_enrollments > 0 else 0
        
        # Get recent enrollments (last 30 days)
        recent_enrollments = db.exec(
            select(func.count(Enrollment.id))
            .where(
                Enrollment.status == "approved",
                Enrollment.is_accessible == True
            )
        ).first()
        
        return {
            "total_courses": total_courses,
            "total_enrollments": total_enrollments,
            "active_enrollments": active_enrollments,
            "recent_enrollments": recent_enrollments,
            "total_revenue": round(total_revenue, 2),
            "completion_rate": round(completion_rate, 2),
            "last_updated": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching dashboard stats: {str(e)}"
        )

@router.get("/courses", response_model=List[AdminCourseList])
async def list_courses(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, ge=1, le=100, description="Number of records to return"),
    status: Optional[str] = Query(None, description="Filter by course status"),
    search: Optional[str] = Query(None, description="Search in course title"),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    """List all courses with pagination and filtering"""
    try:
        query = select(Course)
        
        if status:
            query = query.where(Course.status == status)
        if search:
            query = query.where(Course.title.ilike(f"%{search}%"))
            
        courses = db.exec(query.offset(skip).limit(limit)).all()
        
        result = []
        for course in courses:
            # Get enrollment stats
            total_enrollments = db.exec(
                select(func.count(Enrollment.id))
                .where(Enrollment.course_id == course.id)
            ).first()
            
            active_enrollments = db.exec(
                select(func.count(Enrollment.id))
                .where(
                    Enrollment.course_id == course.id,
                    Enrollment.status == "approved"
                )
            ).first()
            
            # Get average progress
            avg_progress = db.exec(
                select(func.avg(CourseProgress.progress_percentage))
                .where(CourseProgress.course_id == course.id)
            ).first() or 0
            
            result.append(AdminCourseList(
                id=course.id,
                title=course.title,
                price=course.price,
                total_enrollments=total_enrollments,
                active_enrollments=active_enrollments,
                average_progress=round(avg_progress, 2),
                status=course.status,
                created_at=course.created_at,
                updated_at=course.updated_at
            ))
            
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error listing courses: {str(e)}"
        )

@router.get("/courses/{course_id}", response_model=AdminCourseDetail)
async def get_course_detail(
    course_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    """Get detailed information about a specific course"""
    try:
        course = db.exec(
            select(Course)
            .where(Course.id == course_id)
            .options(selectinload(Course.videos))
        ).first()
        
        if not course:
            raise HTTPException(
                status_code=404,
                detail="Course not found"
            )
            
        # Get course statistics
        total_enrollments = db.exec(
            select(func.count(Enrollment.id))
            .where(Enrollment.course_id == course.id)
        ).first()
        
        active_enrollments = db.exec(
            select(func.count(Enrollment.id))
            .where(
                Enrollment.course_id == course.id,
                Enrollment.status == "approved"
            )
        ).first()
        
        completed_enrollments = db.exec(
            select(func.count(CourseProgress.id))
            .where(
                CourseProgress.course_id == course.id,
                CourseProgress.completed == True
            )
        ).first()
        
        avg_progress = db.exec(
            select(func.avg(CourseProgress.progress_percentage))
            .where(CourseProgress.course_id == course.id)
        ).first() or 0
        
        total_revenue = db.exec(
            select(func.sum(Course.price))
            .join(Enrollment)
            .where(
                Enrollment.course_id == course.id,
                Enrollment.status == "approved"
            )
        ).first() or 0
        
        stats = AdminCourseStats(
            total_enrollments=total_enrollments,
            active_enrollments=active_enrollments,
            completed_enrollments=completed_enrollments,
            average_progress=round(avg_progress, 2),
            total_revenue=total_revenue,
            last_updated=datetime.utcnow()
        )
        
        from app.schemas.video import VideoRead
        return AdminCourseDetail(
            id=course.id,
            title=course.title,
            description=course.description,
            price=course.price,
            thumbnail_url=course.thumbnail_url,
            difficulty_level=course.difficulty_level,
            created_by=course.created_by,
            updated_by=course.updated_by,
            created_at=course.created_at,
            updated_at=course.updated_at,
            status=course.status,
            stats=stats,
            videos=[video if isinstance(video, VideoRead) else VideoRead.model_validate(video, from_attributes=True) for video in course.videos]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching course details: {str(e)}"
        )

@router.put("/admin/courses/{course_id}/videos", response_model=List[VideoRead])
def update_course_videos(
    course_id: str,
    videos: List[VideoUpdate],
    user=Depends(get_current_admin_user),
    session: Session = Depends(get_db)
):
    try:
        # Convert course_id to UUID
        course_uuid = uuid.UUID(course_id)
        
        # Check if course exists
        course = session.exec(
            select(Course).where(Course.id == course_uuid)
        ).first()
        
        if not course:
            raise HTTPException(
                status_code=404,
                detail="Course not found"
            )

        # Get existing videos
        existing_videos = session.exec(
            select(Video).where(Video.course_id == course_uuid)
        ).all()
        
        # Track changes
        changes = {
            "deleted_videos": [],
            "added_videos": [],
            "total_videos": len(videos)
        }

        # Delete existing videos and track them
        for video in existing_videos:
            changes["deleted_videos"].append({
                "id": str(video.id),
                "title": video.title,
                "youtube_url": video.youtube_url
            })
            session.delete(video)
        
        # Add new videos and track them
        new_videos = []
        for video_data in videos:
            video = Video(
                course_id=course_uuid,
                youtube_url=video_data.youtube_url,
                title=video_data.title,
                description=video_data.description
            )
            session.add(video)
            new_videos.append(video)
            changes["added_videos"].append({
                "title": video_data.title,
                "youtube_url": video_data.youtube_url
            })

        session.commit()
        session.refresh(course)

        # Return both the updated videos and the changes
        return {
            "videos": new_videos,
            "changes": {
                "deleted_count": len(changes["deleted_videos"]),
                "added_count": len(changes["added_videos"]),
                "total_videos": changes["total_videos"],
                "deleted_videos": changes["deleted_videos"],
                "added_videos": changes["added_videos"]
            }
        }

    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid course ID format"
        )
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while updating course videos: {str(e)}"
        )

from app.utils.email import send_enrollment_approved_email

@router.put("/enrollments/approve")
def approve_enrollment_by_user(
    user_id: str,
    course_id: str,
    duration_months: int = Query(..., description="Duration of access in months"),
    session: Session = Depends(get_db),
    admin=Depends(get_current_admin_user)
):
    # Strip whitespace from IDs to avoid invalid UUID errors
    user_id = user_id.strip()
    course_id = course_id.strip()
    enrollment = session.exec(select(Enrollment).where(Enrollment.user_id == user_id, Enrollment.course_id == course_id)).first()
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    
    # Set enrollment status and access
    enrollment.status = "approved"
    enrollment.is_accessible = True
    
    # Set enrollment date if not set
    if not enrollment.enroll_date:
        enrollment.enroll_date = get_pakistan_time()
    
    # Calculate and set expiration date
    enrollment.expiration_date = enrollment.enroll_date + timedelta(days=30 * duration_months)
    enrollment.update_expiration_status()
    
    session.add(enrollment)
    session.commit()
    
    # Notify student with expiration date
    notif = Notification(
        user_id=enrollment.user_id,
        event_type="enrollment_approved",
        details=f"Enrollment approved for course ID {enrollment.course_id}. Access granted until {enrollment.expiration_date.strftime('%Y-%m-%d %H:%M:%S %Z')} ({enrollment.days_remaining} days remaining)",
    ) 
    session.add(notif)
    session.commit()

    # --- Send enrollment approval email ---
    try:
        # Load relationships if not already loaded
        user = enrollment.user
        course = enrollment.course
        # Defensive fallback if relationships are not loaded
        if user is None:
            from app.models.user import User
            user = session.exec(select(User).where(User.id == enrollment.user_id)).first()
        if course is None:
            from app.models.course import Course
            course = session.exec(select(Course).where(Course.id == enrollment.course_id)).first()
        if user and course:
            send_enrollment_approved_email(
                to_email=user.email,
                course_title=course.title,
                expiration_date=enrollment.expiration_date.strftime('%Y-%m-%d'),
                days_remaining=enrollment.days_remaining or 0
            )
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to send enrollment approval email: {e}")
    # --- End email logic ---

    return {
        "detail": "Enrollment approved and student now has access.",
        "expiration_date": enrollment.expiration_date,
        "days_remaining": enrollment.days_remaining
    }


@router.put("/enrollments/test-expiration")
def test_enrollment_expiration(
    user_id: str,
    course_id: str,
    session: Session = Depends(get_db),
    admin=Depends(get_current_admin_user)
):
    """Test endpoint to set an enrollment's expiration date to today"""
    enrollment = session.exec(select(Enrollment).where(Enrollment.user_id == user_id, Enrollment.course_id == course_id)).first()
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    
    # Set expiration date to today in Pakistan time
    today = get_pakistan_time().replace(hour=0, minute=0, second=0, microsecond=0)
    enrollment.expiration_date = today
    enrollment.update_expiration_status()
    
    session.add(enrollment)
    session.commit()
    
    # Notify student about expiration
    notif = Notification(
        user_id=enrollment.user_id,
        event_type="enrollment_expired",
        details=f"Your enrollment for course ID {enrollment.course_id} has expired today ({today.strftime('%Y-%m-%d %H:%M:%S %Z')})",
    ) 
    session.add(notif)
    session.commit()
    
    return {
        "detail": "Enrollment expiration date set to today",
        "expiration_date": enrollment.expiration_date
    }

@router.post(
    "/admin/courses/{course_id}/assignments",
    response_model=AssignmentRead,
    status_code=201
)
def admin_create_assignment(
    course_id: str,
    payload: AssignmentCreate,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin_user),
):
    """Create a new assignment for a course."""
    try:
        assign = Assignment(
            id=uuid.uuid4(),
            course_id=uuid.UUID(course_id),
            title=payload.title,
            description=payload.description,
            due_date=payload.due_date
        )
        db.add(assign)
        db.commit()
        db.refresh(assign)
        return assign
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Error creating assignment: {e}")

@router.get(
    "/admin/courses/{course_id}/assignments",
    response_model=List[AssignmentRead]
)
def admin_list_assignments(
    course_id: str,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin_user),
):
    """List all assignments under a given course."""
    stmt = select(Assignment).where(Assignment.course_id == uuid.UUID(course_id))
    return db.exec(stmt).all()

@router.delete(
    "/admin/courses/{course_id}/assignments/{assignment_id}",
    status_code=204
)
def admin_delete_assignment(
    course_id: str,
    assignment_id: str,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin_user),
):
    """Remove an assignment."""
    assign = db.get(Assignment, uuid.UUID(assignment_id))
    if not assign or str(assign.course_id) != course_id:
        raise HTTPException(404, "Assignment not found")
    db.delete(assign)
    db.commit()
    return
@router.get(
    "/courses/{course_id}/assignments/{assignment_id}/submissions/students",
    response_model=SubmissionStudentsResponse,
)
def admin_list_on_time_submissions(
    course_id: UUID,
    assignment_id: UUID,
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin_user),
):
    # 1) load assignment
    assignment = db.get(Assignment, assignment_id)
    if not assignment or assignment.course_id != course_id:
        raise HTTPException(404, "Assignment not found")

    # 2) load submissions + students
    stmt = (
        select(AssignmentSubmission)
        .where(
            AssignmentSubmission.assignment_id == assignment_id,
            AssignmentSubmission.submitted_at <= assignment.due_date
        )
        .options(selectinload(AssignmentSubmission.student))
    )
    subs = db.exec(stmt).all()

    students = [
        SubmissionStudent(
            id           = sub.id,
            student_id   = sub.student.id,
            email        = sub.student.email,
            full_name    = sub.student.full_name,
            submitted_at = sub.submitted_at,
            content_url  = sub.content_url,
            grade        = sub.grade,
            feedback     = sub.feedback,
        )
        for sub in subs
    ]

    # 3) return with the correct schema
    return SubmissionStudentsResponse(
        assignment  = AssignmentRead.from_orm(assignment),
        submissions = students,
    ) 

@router.put(
    "/courses/{course_id}/assignments/{assignment_id}/submissions/{submission_id}/grade",
    response_model=SubmissionRead,
    summary="Grade a student's assignment submission",
)
def admin_grade_submission(
    course_id: UUID,
    assignment_id: UUID,
    submission_id: UUID,
    payload: SubmissionGrade,
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin_user),
):
    # 1) Ensure assignment exists under this course
    assignment = db.get(Assignment, assignment_id)
    if not assignment or assignment.course_id != course_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found for this course"
        )

    # 2) Load the submission
    submission = db.get(AssignmentSubmission, submission_id)
    if not submission or submission.assignment_id != assignment_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )

    # 3) Apply grade & feedback
    submission.grade = payload.grade
    submission.feedback = payload.feedback

    db.add(submission)
    db.commit()
    db.refresh(submission)

    # 4) Return the updated submission
    return submission           
@router.put("/courses/{course_id}/assignments/{assignment_id}", response_model=AssignmentRead)
def admin_update_assignment(
    course_id: str,
    assignment_id: str,
    payload: AssignmentCreate,
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin_user),
):
    """Update an assignment's title, description, and due date."""
    assignment = db.get(Assignment, assignment_id)
    if not assignment or str(assignment.course_id) != course_id:
        raise HTTPException(status_code=404, detail="Assignment not found")
    assignment.title = payload.title
    assignment.description = payload.description
    assignment.due_date = payload.due_date
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment

# ──────────────────────────────────────────────────────────────────────────────
# 2. Quiz endpoints
# ──────────────────────────────────────────────────────────────────────────────

@router.post(
    "/admin/courses/{course_id}/quizzes",
    response_model=QuizRead,
    status_code=201
)
def admin_create_quiz(
    course_id: str,
    payload: QuizCreate,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin_user),
):
    """Create a quiz along with its questions & options."""
    try:
        # 1) make the quiz
        quiz = Quiz(
            id=uuid.uuid4(),
            course_id=uuid.UUID(course_id),
            title=payload.title,
            description=payload.description,
        )
        db.add(quiz)
        db.commit()
        db.refresh(quiz)

        # 2) cascade questions + options
        for q in payload.questions:
            question = Question(
                id=uuid.uuid4(),
                quiz_id=quiz.id,
                text=q.text,
                is_multiple_choice=q.is_multiple_choice
            )
            db.add(question)
            db.commit()
            db.refresh(question)

            for opt in q.options:
                option = Option(
                    id=uuid.uuid4(),
                    question_id=question.id,
                    text=opt.text,
                    is_correct=opt.is_correct
                )
                db.add(option)
            db.commit()

        # 3) reload relationships for response
        db.refresh(quiz)
        return quiz

    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Error creating quiz: {e}")

@router.get(
    "/admin/courses/{course_id}/quizzes",
    response_model=List[QuizRead]
)
def admin_list_quizzes(
    course_id: str,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin_user),
):
    """List all quizzes for a course."""
    stmt = select(Quiz).where(Quiz.course_id == uuid.UUID(course_id))
    return db.exec(stmt).all()

@router.delete(
    "/admin/quizzes/{quiz_id}",
    status_code=204
)
def admin_delete_quiz(
    quiz_id: str,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin_user),
):
    """Remove a quiz (and cascade its questions/options via FK cascade)."""
    quiz = db.get(Quiz, uuid.UUID(quiz_id))
    if not quiz:
        raise HTTPException(404, "Quiz not found")

    db.delete(quiz)
    db.commit()
    return   

