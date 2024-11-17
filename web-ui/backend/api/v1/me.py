from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging

from database import get_db, User
from auth import get_current_active_user

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(tags=["user"])


@router.get("/me")
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """
    Get the current user's information
    """
    logger.info(f"Retrieving user info for: {current_user.username}")
    return {
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role,
        "is_active": current_user.is_active,
        "preferences": current_user.preferences if hasattr(current_user, "preferences") else {},
    }
