# File: app/routers/auth_router.py
# File location: src/app/routers/auth_router.py
from fastapi import APIRouter
from ..controllers import auth_controller

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
router.include_router(auth_controller.router) 