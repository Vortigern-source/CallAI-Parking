import os
import sys
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Import local modules directly
from database import Base, User, Booking, get_db, DEFAULT_DATABASE_PATH, DATABASE_URL
from security_config import PasswordValidator

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_database_engine():
    """
    Create SQLAlchemy database engine
    Uses the predefined DATABASE_URL from database module
    """
    logger.info(f"Using database URL: {DATABASE_URL}")
    try:
        engine = create_engine(
            DATABASE_URL,
            connect_args={
                "check_same_thread": False,
            },
        )
        return engine
    except Exception as e:
        logger.error(f"Failed to create database engine: {e}")
        raise


def initialize_database():
    """
    Create all database tables
    """
    try:
        engine = create_database_engine()
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise


def seed_initial_admin():
    """
    Create initial admin user with secure defaults from environment variables
    """
    try:
        # Check for required environment variables
        initial_admin_username = os.getenv("INITIAL_ADMIN_USERNAME")
        initial_admin_email = os.getenv("INITIAL_ADMIN_EMAIL")
        initial_admin_password = os.getenv("INITIAL_ADMIN_PASSWORD")

        if not all([initial_admin_username, initial_admin_email, initial_admin_password]):
            logger.warning("Skipping admin creation: Missing environment variables")
            return

        engine = create_database_engine()
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()

        # Check if admin already exists
        existing_admin = db.query(User).filter(User.username == initial_admin_username).first()
        if existing_admin:
            logger.info(f"Admin user '{initial_admin_username}' already exists. Skipping seeding.")
            db.close()
            return

        # Password validation
        validator = PasswordValidator()
        try:
            validator.validate_password(initial_admin_password)
        except ValueError as e:
            logger.error(f"Initial password validation failed: {e}")
            db.close()
            return

        # Create initial admin user
        hashed_password = pwd_context.hash(initial_admin_password)

        admin_user = User(
            username=initial_admin_username,
            email=initial_admin_email,
            hashed_password=hashed_password,
            role="admin",
            is_active=True,
        )

        try:
            db.add(admin_user)
            db.commit()
            logger.info(f"Initial admin user '{initial_admin_username}' created successfully")
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create admin user: {e}")
        finally:
            db.close()

    except Exception as e:
        logger.error(f"Database seeding failed: {e}")
        raise


def seed_test_bookings():
    """
    Create test bookings for development
    """
    try:
        engine = create_database_engine()
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()

        # Check if test bookings already exist
        existing_bookings = db.query(Booking).count()
        if existing_bookings > 0:
            logger.info("Test bookings already exist. Skipping seeding.")
            db.close()
            return

        # Get admin user
        admin_user = db.query(User).filter(User.role == "admin").first()
        if not admin_user:
            logger.error("No admin user found. Cannot create test bookings.")
            db.close()
            return

        # Create test bookings
        test_bookings = [
            {
                "booking_ref": "PK001",
                "registration": "ABC123",
                "customer_name": "John Smith",
                "terminal": "T1",
                "drop_off_status": "Pending",
                "collection_status": "Not Started",
                "contact_number": "+44123456789",
                "entry_datetime": datetime.now(),
                "return_datetime": datetime.now() + timedelta(days=7),
                "out_flight_number": "BA123",
                "in_flight_number": "BA456",
                "vehicle_make": "Toyota",
                "vehicle_model": "Corolla",
                "allocated_car_park": "Zone A",
            },
            {
                "booking_ref": "PK002",
                "registration": "XYZ789",
                "customer_name": "Jane Doe",
                "terminal": "T2",
                "drop_off_status": "Completed",
                "collection_status": "Pending",
                "contact_number": "+44987654321",
                "entry_datetime": datetime.now() - timedelta(days=3),
                "return_datetime": datetime.now() + timedelta(days=4),
                "out_flight_number": "EK789",
                "in_flight_number": "EK012",
                "vehicle_make": "Honda",
                "vehicle_model": "Civic",
                "allocated_car_park": "Zone B",
            },
        ]

        for booking_data in test_bookings:
            booking = Booking(user_id=admin_user.id, **booking_data)
            db.add(booking)

        try:
            db.commit()
            logger.info("Test bookings created successfully")
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create test bookings: {e}")
        finally:
            db.close()

    except Exception as e:
        logger.error(f"Failed to seed test bookings: {e}")
        raise


def main():
    """
    Main seeding script
    """
    try:
        # Log database path for debugging
        logger.info(f"Database path: {DEFAULT_DATABASE_PATH}")

        # Ensure the database directory exists
        os.makedirs(os.path.dirname(DEFAULT_DATABASE_PATH), exist_ok=True)

        initialize_database()
        seed_initial_admin()
        seed_test_bookings()
        logger.info("Database seeding completed successfully")
    except Exception as e:
        logger.error(f"Database seeding failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
