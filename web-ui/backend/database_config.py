import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# Database configuration utility
class DatabaseConfig:
    """
    Centralized database configuration management
    """

    @staticmethod
    def get_database_url():
        """
        Retrieve database URL from environment or default
        """
        return os.getenv("DATABASE_URL", "sqlite:////app/web-ui-backend/data/parking.db")

    @staticmethod
    def create_engine(database_url=None):
        """
        Create SQLAlchemy engine with configurable options
        """
        if database_url is None:
            database_url = DatabaseConfig.get_database_url()

        return create_engine(
            database_url, connect_args={"check_same_thread": False}, pool_pre_ping=True
        )

    @staticmethod
    def create_session_factory(engine=None):
        """
        Create a session factory with optional custom engine
        """
        if engine is None:
            engine = DatabaseConfig.create_engine()

        return scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

    @staticmethod
    def test_connection(database_url=None):
        """
        Test database connection
        """
        try:
            engine = DatabaseConfig.create_engine(database_url)
            with engine.connect() as connection:
                return True, "Database connection successful"
        except Exception as e:
            return False, f"Database connection failed: {str(e)}"
