from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
import logging

from database import get_db, User
from auth import get_current_active_user, check_admin_role

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/settings", tags=["settings"])


class UserSettings(BaseModel):
    theme: Optional[str] = "light"
    language: Optional[str] = "en"
    notifications: Optional[bool] = True
    dashboard_layout: Optional[Dict[str, Any]] = {}


class GlobalSettings(BaseModel):
    maintenance_mode: Optional[bool] = False
    system_notifications: Optional[str] = ""


@router.get("")
async def get_user_settings(
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
):
    """
    Retrieve user-specific settings
    """
    try:
        # Initialize preferences if they don't exist
        if not current_user.preferences:
            current_user.preferences = {
                "theme": "light",
                "language": "en",
                "notifications": True,
                "dashboard_layout": {},
            }
            db.commit()

        return UserSettings(
            theme=current_user.preferences.get("theme", "light"),
            language=current_user.preferences.get("language", "en"),
            notifications=current_user.preferences.get("notifications", True),
            dashboard_layout=current_user.preferences.get("dashboard_layout", {}),
        )
    except Exception as e:
        logger.error(f"Error retrieving user settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("")
async def update_user_settings(
    settings: UserSettings,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Update user-specific settings
    """
    try:
        # Initialize preferences if they don't exist
        if not current_user.preferences:
            current_user.preferences = {}

        # Update preferences
        current_user.preferences = {
            "theme": settings.theme,
            "language": settings.language,
            "notifications": settings.notifications,
            "dashboard_layout": settings.dashboard_layout,
        }

        # Commit changes to database
        db.add(current_user)
        db.commit()
        db.refresh(current_user)

        logger.info(
            f"Updated settings for user {current_user.username}: {current_user.preferences}"
        )
        return {
            "message": "User settings updated successfully",
            "settings": current_user.preferences,
        }
    except Exception as e:
        logger.error(f"Error updating user settings: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/global")
async def get_global_settings(current_user: User = Depends(check_admin_role)):
    """
    Retrieve global system settings (admin-only)
    """
    try:
        return GlobalSettings(maintenance_mode=False, system_notifications="Welcome to the system")
    except Exception as e:
        logger.error(f"Error retrieving global settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/global")
async def update_global_settings(
    settings: GlobalSettings,
    current_user: User = Depends(check_admin_role),
):
    """
    Update global system settings (admin-only)
    """
    try:
        # In a real implementation, you'd update these in a configuration file or database
        return {"message": "Global settings updated successfully"}
    except Exception as e:
        logger.error(f"Error updating global settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))
