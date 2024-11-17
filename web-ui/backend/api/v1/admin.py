from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import logging

from database import get_db, User
from auth import check_admin_role, get_password_hash
from pydantic import BaseModel, EmailStr, constr

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


class UserResponse(BaseModel):
    username: str
    email: str
    role: str
    is_active: bool


class UserCreate(BaseModel):
    username: constr(min_length=3, max_length=50)
    email: EmailStr
    password: constr(min_length=8)
    role: str = "client"


class UserUpdate(BaseModel):
    is_active: bool = None
    email: EmailStr = None
    role: str = None
    password: str = None


@router.get("/users", response_model=List[UserResponse])
def list_users(current_user: User = Depends(check_admin_role), db: Session = Depends(get_db)):
    """
    List all users (admin-only)
    """
    try:
        users = db.query(User).all()
        return [
            UserResponse(
                username=user.username, email=user.email, role=user.role, is_active=user.is_active
            )
            for user in users
        ]
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error retrieving users"
        )


@router.post("/create-user", response_model=UserResponse)
def create_user(
    user_data: UserCreate,
    current_user: User = Depends(check_admin_role),
    db: Session = Depends(get_db),
):
    """
    Create a new user (admin-only)
    """
    try:
        # Check if username or email already exists
        existing_user = (
            db.query(User)
            .filter((User.username == user_data.username) | (User.email == user_data.email))
            .first()
        )

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username or email already registered",
            )

        # Create new user
        new_user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=get_password_hash(user_data.password),
            role=user_data.role,
            is_active=True,
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return UserResponse(
            username=new_user.username,
            email=new_user.email,
            role=new_user.role,
            is_active=new_user.is_active,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error creating user"
        )


@router.put("/update-user/{username}", response_model=UserResponse)
def update_user(
    username: str,
    user_data: UserUpdate,
    current_user: User = Depends(check_admin_role),
    db: Session = Depends(get_db),
):
    """
    Update user details (admin-only)
    """
    try:
        user = db.query(User).filter(User.username == username).first()

        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        # Prevent modifying admin user's status
        if user.role == "admin" and user_data.is_active is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Cannot modify admin user status"
            )

        # Update fields that are provided
        if user_data.is_active is not None:
            user.is_active = user_data.is_active

        if user_data.email:
            user.email = user_data.email

        if user_data.role:
            user.role = user_data.role

        if user_data.password:
            user.hashed_password = get_password_hash(user_data.password)

        db.commit()
        db.refresh(user)

        return UserResponse(
            username=user.username, email=user.email, role=user.role, is_active=user.is_active
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error updating user"
        )


@router.delete("/delete-user/{username}")
def delete_user(
    username: str, current_user: User = Depends(check_admin_role), db: Session = Depends(get_db)
):
    """
    Delete a user (admin-only)
    """
    try:
        user = db.query(User).filter(User.username == username).first()

        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        # Prevent deleting admin users
        if user.role == "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Cannot delete admin user"
            )

        db.delete(user)
        db.commit()

        return {"message": f"User {username} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error deleting user"
        )
