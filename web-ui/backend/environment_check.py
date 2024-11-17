import os
import sys
from dotenv import load_dotenv


def check_environment():
    """
    Perform comprehensive environment configuration check
    """
    # Load environment variables
    load_dotenv()

    # Check critical environment variables
    critical_vars = [
        "DATABASE_URL",
        "SECRET_KEY",
        "INITIAL_ADMIN_USERNAME",
        "INITIAL_ADMIN_EMAIL",
        "INITIAL_ADMIN_PASSWORD",
    ]

    print("Environment Configuration Check:")
    print("-" * 40)

    for var in critical_vars:
        value = os.getenv(var)
        status = "✓ Set" if value else "✗ Not Set"
        print(f"{var}: {status}")

    # Check Python version
    print(f"\nPython Version: {sys.version}")

    # Check database connection (basic)
    try:
        from sqlalchemy import create_engine

        database_url = os.getenv("DATABASE_URL", "sqlite:///default.db")
        engine = create_engine(database_url)
        with engine.connect() as connection:
            print("Database Connection: ✓ Successful")
    except Exception as e:
        print(f"Database Connection: ✗ Failed - {e}")


def main():
    check_environment()


if __name__ == "__main__":
    main()
