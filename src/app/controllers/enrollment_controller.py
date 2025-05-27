# File: application/src/app/controllers/enrollment_controller.py
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlmodel import Session, select
from app.models.enrollment import Enrollment, get_pakistan_time
from app.models.course import Course
from app.schemas.payment_proof import ProofCreate
from app.db.session import get_db
from app.utils.dependencies import get_current_user
from app.models.payment_proof import PaymentProof
from app.models.notification import Notification
from datetime import datetime, timedelta
import os
from uuid import uuid4
from app.schemas.enrollment import EnrollmentStatus
from app.utils.file import save_upload_and_get_url

router = APIRouter(tags=["Enrollment"])

from app.models.bank_account import BankAccount

@router.get("/courses/{course_id}/purchase-info")
def get_purchase_info(course_id: str, session: Session = Depends(get_db)):
    course = session.exec(select(Course).where(Course.id == course_id)).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    bank_accounts = session.exec(select(BankAccount).where(BankAccount.is_active == True)).all()
    return {
        "course_title": course.title,
        "course_price": course.price,
        "bank_accounts": [
            {
                "bank_name": acc.bank_name,
                "account_name": acc.account_name,
                "account_number": acc.account_number
            }
            for acc in bank_accounts
        ]
    }

@router.post("/enrollments/{course_id}/payment-proof")
def submit_payment_proof(
    course_id: str,
    file: UploadFile = File(...),
    user=Depends(get_current_user),
    session: Session = Depends(get_db)
):
    url = save_upload_and_get_url(file, folder="payment_proofs")
    # Check course
    course = session.exec(select(Course).where(Course.id == course_id)).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    # Create pending enrollment if not exists
    enrollment = session.exec(select(Enrollment).where(Enrollment.user_id == user.id, Enrollment.course_id == course_id)).first()
    if not enrollment:
        enrollment = Enrollment(user_id=user.id, course_id=course_id, status="pending", enroll_date=datetime.utcnow(), is_accessible=False, audit_log=[])
        session.add(enrollment)
        session.commit()
        session.refresh(enrollment)
    # Save payment proof
    payment_proof = PaymentProof(enrollment_id=enrollment.id, proof_url=url)
    session.add(payment_proof)
    session.commit()
    # Notify admin, include user details and picture URL in details
    notif = Notification(
        user_id=user.id,
        event_type="payment_proof",
        details=(
            f"Payment proof submitted for course {course.title}.\n"
            f"User: {user.full_name or user.email} (ID: {user.id})\n"
            f"Email: {user.email}\n"
            f"Proof image: {url}"
        ),
    )
    session.add(notif)
    session.commit()
    return {"detail": "Payment proof submitted, pending admin approval."}

@router.get("/enrollments/{course_id}/status", response_model=EnrollmentStatus)
def check_enrollment_status(course_id: str, user=Depends(get_current_user), session: Session = Depends(get_db)):
    enrollment = session.exec(select(Enrollment).where(Enrollment.user_id == user.id, Enrollment.course_id == course_id)).first()
    if not enrollment:
        return EnrollmentStatus(
            status="not_enrolled",
            message="You are not enrolled in this course.",
            expiration_date=None,
            days_remaining=None,
            is_expired=False,
            is_accessible=False
        )

    # Update enrollment status using Pakistan time
    enrollment.update_expiration_status()
    session.add(enrollment)
    session.commit()

    if enrollment.status == "pending":
        return EnrollmentStatus(
            status="pending",
            message="Your course enrollment is pending admin approval.",
            expiration_date=enrollment.expiration_date,
            days_remaining=enrollment.days_remaining,
            is_expired=enrollment.is_expired,
            is_accessible=enrollment.is_accessible
        )
    
    if enrollment.status == "approved":
        if enrollment.is_expired:
            return EnrollmentStatus(
                status="expired",
                message="Your course access has expired.",
                expiration_date=enrollment.expiration_date,
                days_remaining=0,
                is_expired=True,
                is_accessible=False
            )
        return EnrollmentStatus(
            status="approved",
            message=f"Your course enrollment is approved! {enrollment.days_remaining} days remaining.",
            expiration_date=enrollment.expiration_date,
            days_remaining=enrollment.days_remaining,
            is_expired=False,
            is_accessible=True
        )
    
    return EnrollmentStatus(
        status=enrollment.status,
        message=f"Your enrollment status is {enrollment.status}.",
        expiration_date=enrollment.expiration_date,
        days_remaining=enrollment.days_remaining,
        is_expired=enrollment.is_expired,
        is_accessible=enrollment.is_accessible
    )
