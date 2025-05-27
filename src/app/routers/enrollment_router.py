# File: app/routers/enrollment_router.py
# File location: src/app/routers/enrollment_router.py
from fastapi import APIRouter
from app.controllers import enrollment_controller

router = APIRouter()
router.include_router(enrollment_controller.router) 