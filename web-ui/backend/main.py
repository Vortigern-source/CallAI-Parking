from fastapi import FastAPI, HTTPException, Depends, status, Request, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from datetime import timedelta
import os
import sys
import pathlib
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=env_path)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Add the backend directory to Python path
current_dir = str(pathlib.Path(__file__).parent.absolute())
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
    logger.info(f"Added backend directory to Python path: {current_dir}")

# Add the project root to Python path for functions module
project_root = str(pathlib.Path(__file__).parent.parent.parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    logger.info(f"Added project root to Python path: {project_root}")

from database import get_db, create_initial_admin
from auth import (
    authenticate_user,
    create_access_token,
    get_current_active_user,
    check_admin_role,
    Token,
    pwd_context,
    User,
)
from api.v1.auth import router as auth_router
from api.v1.bookings import router as bookings_router
from api.v1.bot_config import router as bot_config_router
from api.v1.settings import router as settings_router
from api.v1.admin import router as admin_router
from api.v1.dashboard import router as dashboard_router
from api.v1.me import router as me_router
from init_db import init_db

app = FastAPI()

# Get allowed origins from environment variable
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

logger.info(f"Allowed origins: {ALLOWED_ORIGINS}")
logger.info("Environment variables loaded:")
for key in os.environ:
    if not key.startswith("_"):  # Skip internal env vars
        logger.info(f"{key}: {os.getenv(key)}")

# Enable CORS with more detailed configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Create API v1 router
api_v1_router = APIRouter(prefix="/api/v1")

# Include routers under API v1
api_v1_router.include_router(auth_router)
api_v1_router.include_router(bookings_router)
api_v1_router.include_router(bot_config_router)
api_v1_router.include_router(settings_router)
api_v1_router.include_router(admin_router)
api_v1_router.include_router(dashboard_router)
api_v1_router.include_router(me_router)

# Log all registered routes
logger.info("Registered routes:")
for route in api_v1_router.routes:
    logger.info(f"{route.path} - {route.methods}")

# Include API v1 router in main app
app.include_router(api_v1_router)

# Set up static files directory
static_dir = os.path.join(current_dir, "static")
logger.info(f"Static directory path: {static_dir}")

# Ensure static directory exists
if not os.path.exists(static_dir):
    try:
        os.makedirs(static_dir, exist_ok=True)
        logger.info(f"Created static directory at: {static_dir}")
    except Exception as e:
        logger.error(f"Failed to create static directory: {e}")
        raise


# Function to serve static files
async def serve_static_file(filepath: str):
    # Check if the file exists in the static/static directory first
    full_path = os.path.join(static_dir, "static", filepath)
    if os.path.exists(full_path) and os.path.isfile(full_path):
        logger.info(f"Serving file from static/static: {full_path}")
        return FileResponse(full_path)

    # If not found in static/static, check in the root static directory
    full_path = os.path.join(static_dir, filepath)
    if os.path.exists(full_path) and os.path.isfile(full_path):
        logger.info(f"Serving file from static root: {full_path}")
        return FileResponse(full_path)

    logger.error(f"File not found: {filepath}")
    logger.error(f"Tried paths:")
    logger.error(f"1. {os.path.join(static_dir, 'static', filepath)}")
    logger.error(f"2. {os.path.join(static_dir, filepath)}")
    raise HTTPException(status_code=404, detail="File not found")


# Serve static files
@app.get("/static/{filepath:path}")
async def serve_static(filepath: str):
    logger.info(f"Serving static file: {filepath}")
    return await serve_static_file(filepath)


# Serve manifest.json
@app.get("/manifest.json")
async def serve_manifest():
    manifest_path = os.path.join(static_dir, "manifest.json")
    if os.path.exists(manifest_path):
        return FileResponse(manifest_path)
    return JSONResponse(content={})


# Serve index.html for root path
@app.get("/")
async def serve_root():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        logger.info("Attempting to serve index.html from: " + index_path)
        logger.info("index.html found, serving file")
        content = open(index_path, "r").read()
        logger.info(f"Successfully read index.html, content length: {len(content)}")
        return FileResponse(index_path)
    logger.error(f"index.html not found at: {index_path}")
    raise HTTPException(status_code=404, detail="index.html not found")


# Serve index.html for all other non-API routes
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    # Explicitly allow /start_call to pass through
    if full_path == "start_call":
        raise HTTPException(status_code=404, detail="Not found for this service")

    # If the path starts with "api/", let the API router handle it
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="Not found")

    # For all other paths, serve index.html
    return await serve_root()


@app.on_event("startup")
async def startup_event():
    """
    Initialize database and create initial admin user on startup
    """
    try:
        # Initialize database
        logger.info("Initializing database...")
        init_db()
        logger.info("Database initialization completed")

        # Log static directory structure
        logger.info("Static directory structure at startup:")
        if os.path.exists(static_dir):
            for root, dirs, files in os.walk(static_dir):
                rel_path = os.path.relpath(root, static_dir)
                logger.info(f"Directory: {rel_path}")
                for file in files:
                    logger.info(f"File: {os.path.join(rel_path, file)}")
        else:
            logger.warning("Static directory not found at startup")

    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
