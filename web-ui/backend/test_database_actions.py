import os
import sys
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pytest
from passlib.context import CryptContext

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import Base, User, get_db, DATABASE_URL
from auth import authenticate_user, get_password_hash

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_test_engine():
    """Create a test database engine"""
    return create_engine(DATABASE_URL)


def create_test_session():
    """Create a test database session"""
    engine = create_test_engine()
    TestSessionLocal = sessionmaker(bind=engine)
    return TestSessionLocal()


def test_initial_admin_creation():
    """Test initial admin user creation"""
    db = create_test_session()

    # Set test admin credentials
    test_username = "test_admin"
    test_email = "test_admin@example.com"
    test_password = "TestAdminPassword123!"

    # Check if admin already exists
    existing_admin = db.query(User).filter(User.username == test_username).first()
    if existing_admin:
        db.delete(existing_admin)
        db.commit()

    # Create admin user
    hashed_password = get_password_hash(test_password)
    admin_user = User(
        username=test_username,
        email=test_email,
        hashed_password=hashed_password,
        role="admin",
        is_active=True,
    )

    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)

    # Verify admin user creation
    assert admin_user.username == test_username
    assert admin_user.email == test_email
    assert admin_user.role == "admin"
    assert admin_user.is_active == True

    logger.info(f"Initial admin user {test_username} created successfully")
    db.close()


def test_user_authentication():
    """Test user authentication"""
    db = create_test_session()

    # Use the test admin credentials from previous test
    test_username = "test_admin"
    test_password = "TestAdminPassword123!"

    # Attempt authentication
    authenticated_user = authenticate_user(db, test_username, test_password)

    assert authenticated_user is not False
    assert authenticated_user.username == test_username

    logger.info(f"User {test_username} authenticated successfully")
    db.close()


def test_add_multiple_users():
    """Test adding multiple users"""
    db = create_test_session()

    test_users = [
        {
            "username": "user1",
            "email": "user1@example.com",
            "password": "UserPassword123!",
            "role": "client",
        },
        {
            "username": "user2",
            "email": "user2@example.com",
            "password": "UserPassword456!",
            "role": "client",
        },
    ]

    created_users = []
    for user_data in test_users:
        # Check if user already exists
        existing_user = (
            db.query(User)
            .filter((User.username == user_data["username"]) | (User.email == user_data["email"]))
            .first()
        )

        if existing_user:
            db.delete(existing_user)
            db.commit()

        # Create new user
        new_user = User(
            username=user_data["username"],
            email=user_data["email"],
            hashed_password=get_password_hash(user_data["password"]),
            role=user_data["role"],
            is_active=True,
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        created_users.append(new_user)

    # Verify user creation
    assert len(created_users) == 2
    for user in created_users:
        assert user.is_active == True
        assert user.role == "client"

    logger.info("Multiple users created successfully")
    db.close()


def test_fetch_all_users():
    """Test fetching all users"""
    db = create_test_session()

    # Fetch all users
    users = db.query(User).all()

    assert len(users) > 0

    logger.info(f"Fetched {len(users)} users successfully")

    # Print user details for verification
    for user in users:
        logger.info(f"User: {user.username}, Email: {user.email}, Role: {user.role}")

    db.close()


def main():
    """Run all database action tests"""
    try:
        test_initial_admin_creation()
        test_user_authentication()
        test_add_multiple_users()
        test_fetch_all_users()
        print("All database action tests passed successfully!")
    except Exception as e:
        print(f"Test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
