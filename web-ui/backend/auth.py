from datetime import datetime, timedelta
from typing import Optional
import os
import secrets
import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db, User
from security_config import PasswordValidator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "835cd2e5d2c9b3a7f9e1d4b8a6c2e5f8")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

# Password hashing context - must match init_db.py
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,  # Explicitly set rounds
)

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


# Token model for Swagger/OpenAPI
class Token(BaseModel):
    access_token: str
    token_type: str
    role: str


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain text password against its hashed version
    """
    try:
        logger.info("Starting password verification")

        # Clean the password
        plain_password = plain_password.strip()

        # Log details for debugging
        logger.info(f"Plain password length: {len(plain_password)}")
        logger.info(f"Hashed password length: {len(hashed_password)}")

        # Create a test hash for comparison
        test_hash = pwd_context.hash("AdminInitialPassword123!")
        logger.info(f"Test hash length: {len(test_hash)}")

        # Verify the password
        result = pwd_context.verify(plain_password, hashed_password)
        logger.info(f"Password verification result: {result}")

        # If verification failed, try to identify why
        if not result:
            test_verify = pwd_context.verify("AdminInitialPassword123!", hashed_password)
            logger.info(f"Test verification with known password: {test_verify}")

        return result
    except Exception as e:
        logger.error(f"Password verification error: {str(e)}")
        return False


def get_password_hash(password: str) -> str:
    """
    Hash a password for storing
    """
    try:
        # Clean the password
        password = password.strip()
        hashed = pwd_context.hash(password)
        logger.info(f"Password hashed successfully. Hash length: {len(hashed)}")
        return hashed
    except Exception as e:
        logger.error(f"Password hashing error: {str(e)}")
        raise


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """
    Retrieve a user by username
    """
    logger.info(f"Looking up user: {username}")
    user = db.query(User).filter(User.username == username).first()
    logger.info(f"User found: {user is not None}")
    if user:
        logger.info(f"User role: {user.role}")
        logger.info(f"User is_active: {user.is_active}")
        logger.info(f"User hashed_password length: {len(user.hashed_password)}")
    return user


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """
    Authenticate a user
    """
    logger.info(f"Attempting to authenticate user: {username}")
    user = get_user_by_username(db, username)
    if not user:
        logger.warning("User not found")
        return False

    logger.info("Verifying password")
    if not verify_password(password, user.hashed_password):
        logger.warning("Invalid password")
        return False

    logger.info("Authentication successful")
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    logger.info(f"Created access token for user: {data.get('sub')}")
    return encoded_jwt


def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:
    """
    Get the current authenticated user from a JWT token
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            logger.error("No username found in token")
            raise credentials_exception
    except JWTError as e:
        logger.error(f"JWT error: {str(e)}")
        raise credentials_exception

    user = get_user_by_username(db, username)
    if user is None:
        logger.error("User not found in database")
        raise credentials_exception
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Get the current active user
    """
    if not current_user.is_active:
        logger.error(f"Inactive user attempted access: {current_user.username}")
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def check_admin_role(current_user: User = Depends(get_current_active_user)) -> User:
    """
    Check if the current user has admin role
    """
    if current_user.role != "admin":
        logger.error(f"Non-admin user attempted admin action: {current_user.username}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation not permitted. Admin access required.",
        )
    return current_user
