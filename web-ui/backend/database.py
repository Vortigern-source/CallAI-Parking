from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
import sys
import logging
import json

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


# Determine the appropriate data directory
def get_data_directory():
    """Get or create a data directory"""
    # Use local data directory instead of Docker's /app
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(current_dir, "data")

    try:
        # Create directory with proper permissions
        os.makedirs(data_dir, mode=0o777, exist_ok=True)
        logger.info(f"Using data directory: {data_dir}")
        return data_dir
    except Exception as e:
        logger.error(f"Error creating data directory: {e}")
        raise


# Database Configuration
DEFAULT_DATABASE_PATH = os.path.join(get_data_directory(), "parking.db")
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DATABASE_PATH}")

# Detailed logging of database configuration
logger.info(f"Database URL: {DATABASE_URL}")
logger.info(f"Database Path: {DEFAULT_DATABASE_PATH}")

# Create SQLAlchemy engine with appropriate settings for SQLite
try:
    # Extract the actual database file path from the URL
    db_path = DATABASE_URL.replace("sqlite:///", "")
    logger.info(f"Actual database path: {db_path}")

    # Ensure the database directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    engine = create_engine(
        DATABASE_URL,
        connect_args={
            "check_same_thread": False,  # Required for SQLite in multi-threaded environments
        },
        pool_pre_ping=True,  # Helps with connection reliability
    )
    logger.info("Database engine created successfully")
except Exception as e:
    logger.critical(f"Failed to create database engine: {e}")
    raise

# Create a SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a Base class for declarative models
Base = declarative_base()


# User Model
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="client")
    is_active = Column(Boolean, default=True)
    preferences = Column(
        JSON,
        default=lambda: {
            "theme": "light",
            "language": "en",
            "notifications": True,
            "dashboard_layout": {},
        },
    )
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    # Relationship with bookings
    bookings = relationship("Booking", back_populates="user")

    def __repr__(self):
        return f"<User {self.username}>"


# Booking Model
class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    booking_ref = Column(String, unique=True, index=True, nullable=False)
    registration = Column(String, nullable=False)
    customer_name = Column(String, nullable=False)
    terminal = Column(String, nullable=True)
    drop_off_status = Column(String, default="Not Set")
    collection_status = Column(String, default="Not Set")
    contact_number = Column(String, nullable=True)
    entry_datetime = Column(DateTime, nullable=False)
    return_datetime = Column(DateTime, nullable=False)
    out_flight_number = Column(String, nullable=True)
    in_flight_number = Column(String, nullable=True)
    vehicle_make = Column(String, nullable=True)
    vehicle_model = Column(String, nullable=True)
    allocated_car_park = Column(String, nullable=True)
    product_code = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship with user
    user = relationship("User", back_populates="bookings")

    def __repr__(self):
        return f"<Booking {self.booking_ref}>"


try:
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")
except Exception as e:
    logger.error(f"Error creating database tables: {e}")
    raise


# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Initial admin user creation function
def create_initial_admin(db, username, email, hashed_password):
    """
    Create the first admin user if no admin exists
    """
    try:
        existing_admin = db.query(User).filter(User.role == "admin").first()
        logger.info(
            f"Checking for existing admin user: {'Found' if existing_admin else 'Not found'}"
        )

        if not existing_admin:
            admin_user = User(
                username=username,
                email=email,
                hashed_password=hashed_password,
                role="admin",
                is_active=True,
                preferences={
                    "theme": "light",
                    "language": "en",
                    "notifications": True,
                    "dashboard_layout": {},
                },
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
            logger.info(f"Initial admin user created successfully: {username}")
            return admin_user

        logger.info("Admin user already exists")
        return None
    except Exception as e:
        logger.error(f"Error creating initial admin user: {e}")
        db.rollback()
        raise
