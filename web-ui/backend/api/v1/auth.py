from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from sqlalchemy.orm import Session
from datetime import timedelta
import logging

from database import get_db
from auth import authenticate_user, create_access_token, get_current_active_user, Token, User

router = APIRouter(prefix="/auth", tags=["authentication"])

# Configure logging
logger = logging.getLogger(__name__)


@router.post("/token", response_model=Token)
async def login_for_access_token(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    """
    OAuth2 compatible token login endpoint with enhanced logging
    """
    try:
        # Log incoming request details
        logger.info("Received login request")
        logger.info(f"Username attempt: {username}")

        # Clean input
        username = username.strip()
        password = password.strip()

        # Authenticate user
        user = authenticate_user(db, username, password)
        if not user:
            logger.warning(f"Invalid login attempt for user: {username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Create access token
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=timedelta(minutes=30)
        )

        logger.info(f"Successful login for user: {user.username}")

        # Return token with additional user information
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "role": user.role,
            "username": user.username,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred",
        )


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
    }
