from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db, User
from auth import get_current_active_user, check_admin_role, get_password_hash
from pydantic import BaseModel, EmailStr, constr, Field
from datetime import datetime
from typing import List

admin_router = APIRouter(prefix="/admin", tags=["admin"])


class UserCreate(BaseModel):
    username: constr(min_length=3, max_length=50)
    email: EmailStr
    password: constr(min_length=8)
    role: str = "client"


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    is_active: bool
    created_at: datetime


@admin_router.post("/users")
def create_user(
    user: UserCreate, current_user: User = Depends(check_admin_role), db: Session = Depends(get_db)
):
    """
    Create a new user (admin-only)
    """
    # Check if username already exists
    existing_user = (
        db.query(User).filter((User.username == user.username) | (User.email == user.email)).first()
    )

    if existing_user:
        raise HTTPException(status_code=400, detail="Username or email already registered")

    # Create new user
    new_user = User(
        username=user.username,
        email=user.email,
        hashed_password=get_password_hash(user.password),
        role=user.role,
        is_active=True,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User created successfully"}


@admin_router.put("/users/{user_id}/status")
def update_user_status(
    user_id: int,
    is_active: bool,
    current_user: User = Depends(check_admin_role),
    db: Session = Depends(get_db),
):
    """
    Update user active status (admin-only)
    """
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = is_active
    db.commit()

    return {"message": f"User {'activated' if is_active else 'deactivated'} successfully"}


@admin_router.get("/users", response_model=List[UserResponse])
def list_users(current_user: User = Depends(check_admin_role), db: Session = Depends(get_db)):
    """
    List all users (admin-only)
    """
    users = db.query(User).all()
    return [
        UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
        )
        for user in users
    ]
