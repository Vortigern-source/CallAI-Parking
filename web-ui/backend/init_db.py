import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext
from database import Base, User, DATABASE_URL

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Password hashing context - must match the one in auth.py
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,  # Explicitly set rounds
)


def init_db():
    """Initialize database and create/update admin user"""
    try:
        logger.info(f"Initializing database with URL: {DATABASE_URL}")

        # Ensure data directory exists
        data_dir = os.path.dirname(DATABASE_URL.replace("sqlite:///", ""))
        if not os.path.exists(data_dir):
            os.makedirs(data_dir, exist_ok=True)
            logger.info(f"Created data directory: {data_dir}")

        # Create engine
        engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

        # Create tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")

        # Create session
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()

        # Get admin credentials from environment
        admin_username = os.getenv("INITIAL_ADMIN_USERNAME", "admin")
        admin_password = os.getenv("INITIAL_ADMIN_PASSWORD", "AdminInitialPassword123!")
        admin_email = os.getenv("INITIAL_ADMIN_EMAIL", "admin@callgpt-parking.local")

        # Log the password details (not the actual password)
        logger.info(f"Admin username: {admin_username}")
        logger.info(f"Admin email: {admin_email}")
        logger.info(f"Admin password length: {len(admin_password)}")

        # Create password hash
        hashed_password = pwd_context.hash(admin_password)
        logger.info(f"Generated hash length: {len(hashed_password)}")

        # Verify the hash works
        verify_result = pwd_context.verify(admin_password, hashed_password)
        logger.info(f"Initial hash verification: {verify_result}")

        # Check if admin exists
        admin = db.query(User).filter(User.username == admin_username).first()

        if not admin:
            # Create admin user
            logger.info("Creating new admin user")
            admin = User(
                username=admin_username,
                email=admin_email,
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

            db.add(admin)
            db.commit()
            logger.info("Admin user created successfully")
        else:
            # Update admin user
            logger.info("Updating existing admin user")
            admin.hashed_password = hashed_password
            admin.email = admin_email
            db.commit()
            logger.info("Admin user updated")

            # Verify the update
            updated_admin = db.query(User).filter(User.username == admin_username).first()
            verify_result = pwd_context.verify(admin_password, updated_admin.hashed_password)
            logger.info(f"Updated hash verification: {verify_result}")
            logger.info(f"Stored hash length: {len(updated_admin.hashed_password)}")

        # Test password verification
        test_admin = db.query(User).filter(User.username == admin_username).first()
        test_verify = pwd_context.verify(admin_password, test_admin.hashed_password)
        logger.info(f"Final verification test: {test_verify}")

        db.close()
        logger.info("Database initialization completed successfully")

    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise


if __name__ == "__main__":
    init_db()
