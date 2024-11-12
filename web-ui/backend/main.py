from fastapi import FastAPI, HTTPException, Query, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import os
from datetime import datetime, timedelta
import glob
from dotenv import load_dotenv, set_key, find_dotenv
import re
import pytz
import ast
import astor
import inspect
import aiohttp
from urllib.parse import quote
import logging
from auth import (
    Token,
    User,
    authenticate_user,
    create_access_token,
    get_current_active_user,
    check_admin_role,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()

# Load environment variables
dotenv_path = find_dotenv()
load_dotenv(dotenv_path)

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_BOOKINGS_TABLE = os.getenv("AIRTABLE_BOOKINGS_TABLE")

logger.debug(f"Airtable Config - Base ID: {AIRTABLE_BASE_ID}, Table: {AIRTABLE_BOOKINGS_TABLE}")

# Load params.json for file paths
with open("../../params.json") as f:
    params = json.load(f)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Authentication endpoints
@app.post("/api/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "role": user.role}


@app.get("/api/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Get current user information."""
    return current_user


# Models
class CallLog(BaseModel):
    id: str
    timestamp: str
    phoneNumber: str
    duration: str
    status: str


class Booking(BaseModel):
    id: str
    registration: str
    customerName: str
    terminal: str
    dropOffStatus: str
    collectionStatus: str
    contactNumber: str
    entryDateTime: str
    returnDateTime: str
    currentETA: str
    vehicleMake: str
    allocatedCarPark: str
    bookingRef: str
    outFlightNumber: str
    inFlightNumber: str
    productCode: str


class Settings(BaseModel):
    # Twilio Settings
    twilioAccountSid: str
    twilioAuthToken: str
    fromNumber: str
    appNumber: str
    yourNumber: str
    twilioWhatsappNumber: str
    managerWhatsappGroup: str
    server: str

    # Service API Keys
    openaiApiKey: str
    deepgramApiKey: str
    groqApiKey: str
    cartesiaApiKey: str
    notionApiKey: str
    notionPageId: str
    xiApiKey: str
    xiModelId: str
    xiVoiceId: str
    gladiaApiKey: str
    playhtUserId: str
    playhtApiKey: str
    azureSpeechKey: str
    azureSpeechRegion: str

    # Airtable Settings
    airtableApiKey: str
    airtableBaseId: str
    airtableBookingsTable: str
    airtableDeparturesTable: str
    airtableArrivalsTable: str

    # Voice and Recording Settings
    voiceModel: str
    recordingEnabled: bool

    # Bot Settings
    welcomeMessage: str
    assistantPrompt: str
    enableInterruptions: bool
    enableMetrics: bool


class Function(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Dict[str, str]]
    implementation: str


# Environment variable mapping
ENV_MAPPING = {
    "twilioAccountSid": "TWILIO_ACCOUNT_SID",
    "twilioAuthToken": "TWILIO_AUTH_TOKEN",
    "fromNumber": "FROM_NUMBER",
    "appNumber": "APP_NUMBER",
    "yourNumber": "YOUR_NUMBER",
    "twilioWhatsappNumber": "TWILIO_WHATSAPP_NUMBER",
    "managerWhatsappGroup": "MANAGER_WHATSAPP_GROUP",
    "server": "SERVER",
    "openaiApiKey": "OPENAI_API_KEY",
    "deepgramApiKey": "DEEPGRAM_API_KEY",
    "groqApiKey": "GROQ_API_KEY",
    "cartesiaApiKey": "CARTESIA_API_KEY",
    "notionApiKey": "NOTION_API_KEY",
    "notionPageId": "NOTION_PAGE_ID",
    "xiApiKey": "XI_API_KEY",
    "xiModelId": "XI_MODEL_ID",
    "xiVoiceId": "XI_VOICE_ID",
    "gladiaApiKey": "GLADIA_API_KEY",
    "playhtUserId": "PLAYHT_USER_ID",
    "playhtApiKey": "PLAYHT_API_KEY",
    "azureSpeechKey": "AZURE_SPEECH_KEY",
    "azureSpeechRegion": "AZURE_SPEECH_REGION",
    "airtableApiKey": "AIRTABLE_API_KEY",
    "airtableBaseId": "AIRTABLE_BASE_ID",
    "airtableBookingsTable": "AIRTABLE_BOOKINGS_TABLE",
    "airtableDeparturesTable": "AIRTABLE_DEPARTURES_TABLE",
    "airtableArrivalsTable": "AIRTABLE_ARRIVALS_TABLE",
    "voiceModel": "VOICE_MODEL",
    "recordingEnabled": "RECORDING_ENABLED",
}


def format_date_for_formula(date_obj: datetime) -> str:
    """Format datetime object for Airtable formula (D/M/YYYY HH:mm)"""
    return date_obj.strftime("%-d/%-m/%Y %H:%M")


def parse_log_file(file_path: str) -> Dict:
    """Parse a log file and extract relevant information."""
    with open(file_path, "r") as f:
        content = f.read()

    # Extract timestamp from filename or first log entry
    timestamp_match = re.search(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", content)
    timestamp = timestamp_match.group(0) if timestamp_match else "Unknown"

    # Extract phone number
    phone_match = re.search(r"Call from (\+?\d[\d-]+)", content)
    phone_number = phone_match.group(1) if phone_match else "Unknown"

    # Determine call status and duration
    if "Customer has ended call" in content:
        status = "Completed"
        # Try to calculate duration
        start_time = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
        end_match = re.search(
            r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*Customer has ended call", content
        )
        if end_match:
            end_time = datetime.strptime(end_match.group(1), "%Y-%m-%d %H:%M:%S")
            duration = str(end_time - start_time)
        else:
            duration = "Unknown"
    else:
        status = "In Progress"
        duration = "Ongoing"

    return {
        "id": os.path.basename(file_path),
        "timestamp": timestamp,
        "phoneNumber": phone_number,
        "duration": duration,
        "status": status,
    }


def get_call_logs() -> List[Dict]:
    """Get all call logs from the logs directory."""
    logs_dir = os.path.join("..", "..", params["file_paths"]["logs"])
    log_files = glob.glob(os.path.join(logs_dir, f"*{params['file_extensions']['log']}"))

    logs = []
    for file_path in log_files:
        try:
            log_data = parse_log_file(file_path)
            logs.append(log_data)
        except Exception as e:
            print(f"Error parsing log file {file_path}: {str(e)}")

    return sorted(logs, key=lambda x: x["timestamp"], reverse=True)


def get_functions() -> List[Dict]:
    """Get all bot functions from the functions directory."""
    functions = []
    functions_dir = os.path.join("..", "..", "functions")

    # Skip these files
    skip_files = {"__init__.py", "__pycache__"}

    for file in os.listdir(functions_dir):
        if file.endswith(".py") and file not in skip_files:
            try:
                with open(os.path.join(functions_dir, file), "r") as f:
                    content = f.read()

                # Parse the Python file
                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # Get function docstring
                        docstring = ast.get_docstring(node) or "No description available"

                        # Get function parameters
                        params = {}
                        for arg in node.args.args:
                            if arg.arg != "self":  # Skip self parameter for methods
                                # Try to get type hint
                                type_hint = ""
                                if arg.annotation and isinstance(arg.annotation, ast.Name):
                                    type_hint = arg.annotation.id

                                params[arg.arg] = {
                                    "type": type_hint,
                                    "description": "Parameter description not available",
                                }

                        # Get function implementation
                        implementation = astor.to_source(node)

                        functions.append(
                            {
                                "name": node.name,
                                "description": docstring,
                                "parameters": params,
                                "implementation": implementation,
                            }
                        )
            except Exception as e:
                logger.error(f"Error parsing function file {file}: {str(e)}")

    return functions


async def get_airtable_bookings(
    status: Optional[str] = None,
    terminal: Optional[str] = None,
    search: Optional[str] = None,
    active_only: bool = False,
) -> List[Dict]:
    """Get all bookings from Airtable with optional filters."""
    try:
        headers = {
            "Authorization": f"Bearer {AIRTABLE_API_KEY}",
            "Content-Type": "application/json",
        }

        # Build filter formula
        formula_parts = []

        # Status filter
        if status and status != "all":
            status_field = (
                "Drop_Off_Status" if "drop_off" in status.lower() else "Collection_Status"
            )
            formula_parts.append(f'{{{status_field}}} = "{status}"')

        # Terminal filter
        if terminal and terminal != "all":
            formula_parts.append(f'{{Terminal}} = "{terminal}"')

        # Search filter
        if search:
            search = search.upper()
            formula_parts.append(
                f'OR(UPPER({{Registration}}) = "{search}", ' f'UPPER({{Name}}) = "{search}")'
            )

        # Active bookings filter
        if active_only:
            current_time = datetime.now(pytz.timezone("Europe/London"))
            current_str = format_date_for_formula(current_time)
            past_24h_str = format_date_for_formula(current_time - timedelta(hours=24))
            next_24h_str = format_date_for_formula(current_time + timedelta(hours=24))

            active_formula = (
                "OR("
                "AND("
                f'IS_BEFORE({{Entry_Date_Time}}, "{current_str}", "Europe/London"), '
                f'IS_AFTER({{Return_Date_Time}}, "{current_str}", "Europe/London")'
                "), "
                "AND("
                f'IS_AFTER({{Entry_Date_Time}}, "{past_24h_str}", "Europe/London"), '
                f'IS_BEFORE({{Return_Date_Time}}, "{next_24h_str}", "Europe/London")'
                ")"
                ")"
            )
            formula_parts.append(active_formula)

        # Combine all formula parts
        formula = None
        if formula_parts:
            formula = " AND ".join(formula_parts)

        # Build URL
        url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_BOOKINGS_TABLE}?"

        if formula:
            url += f"filterByFormula={quote(formula)}&"

        url += "cellFormat=string&" "timeZone=Europe/London&" "userLocale=en-gb"

        logger.debug(f"Making Airtable request to: {url}")

        bookings = []
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                logger.debug(f"Airtable response status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    logger.debug(f"Airtable response data: {json.dumps(data, indent=2)}")

                    for record in data.get("records", []):
                        fields = record.get("fields", {})
                        # Only include records with required fields
                        if fields.get("Registration") and fields.get("Name"):
                            booking = {
                                "id": record["id"],
                                "registration": fields.get("Registration", "Unknown"),
                                "customerName": fields.get("Name", "Unknown"),
                                "terminal": fields.get("Terminal", "Unknown"),
                                "dropOffStatus": fields.get("Drop_Off_Status", "Not Set"),
                                "collectionStatus": fields.get("Collection_Status", "Not Set"),
                                "contactNumber": fields.get("Contact_Number", "Unknown"),
                                "entryDateTime": fields.get("Entry_Date_Time", "Unknown"),
                                "returnDateTime": fields.get("Return_Date_Time", "Unknown"),
                                "currentETA": fields.get("Current_ETA", "N/A"),
                                "vehicleMake": fields.get("Vehicle_Make", "Unknown"),
                                "allocatedCarPark": fields.get("Allocated_Car_Park", "Unknown"),
                                "bookingRef": fields.get("Booking_Ref", "Unknown"),
                                "outFlightNumber": fields.get("Out Flight Number", "Unknown"),
                                "inFlightNumber": fields.get("In Flight Number", "Unknown"),
                                "productCode": fields.get("Product_Code", "Unknown"),
                            }
                            bookings.append(booking)
                else:
                    error_text = await response.text()
                    logger.error(f"Error from Airtable: {error_text}")

        logger.debug(f"Returning {len(bookings)} bookings")
        return bookings
    except Exception as e:
        logger.exception("Error fetching Airtable bookings")
        return []


@app.get("/api/calls", response_model=List[CallLog])
async def get_calls(current_user: User = Depends(check_admin_role)):
    """Get all call logs. Admin only."""
    return get_call_logs()


@app.get("/api/functions", response_model=List[Function])
async def get_bot_functions(current_user: User = Depends(check_admin_role)):
    """Get all bot functions. Admin only."""
    return get_functions()


@app.get("/api/bookings", response_model=List[Booking])
async def get_bookings(
    status: Optional[str] = Query(None, description="Filter by status"),
    terminal: Optional[str] = Query(None, description="Filter by terminal"),
    search: Optional[str] = Query(None, description="Search by registration or customer name"),
    active: bool = Query(False, description="Show only active bookings"),
    current_user: User = Depends(get_current_active_user),
):
    """Get all bookings from Airtable with optional filters."""
    logger.debug(
        f"Received booking request - status: {status}, terminal: {terminal}, search: {search}, active: {active}"
    )
    bookings = await get_airtable_bookings(status, terminal, search, active)
    logger.debug(f"Returning {len(bookings)} bookings")
    return bookings


@app.get("/api/stats")
async def get_stats(current_user: User = Depends(get_current_active_user)):
    """Get system statistics."""
    try:
        calls = get_call_logs() if current_user.role == "admin" else []
        bookings = await get_airtable_bookings(active_only=True)

        # Calculate total calls today (admin only)
        if current_user.role == "admin":
            today = datetime.now().date()
            total_calls_today = sum(
                1
                for call in calls
                if datetime.strptime(call["timestamp"], "%Y-%m-%d %H:%M:%S").date() == today
            )

            # Calculate average call duration
            completed_calls = [
                call
                for call in calls
                if call["status"] == "Completed" and call["duration"] != "Unknown"
            ]
            if completed_calls:
                durations = []
                for call in completed_calls:
                    try:
                        time_parts = call["duration"].split(":")
                        seconds = (
                            int(time_parts[0]) * 3600
                            + int(time_parts[1]) * 60
                            + float(time_parts[2])
                        )
                        durations.append(seconds)
                    except:
                        continue

                if durations:
                    avg_duration_secs = sum(durations) / len(durations)
                    avg_duration = f"{int(avg_duration_secs // 60)}m {int(avg_duration_secs % 60)}s"
                else:
                    avg_duration = "Unknown"
            else:
                avg_duration = "Unknown"

            # Calculate call volume by hour
            call_volume = {}
            for call in calls:
                try:
                    hour = datetime.strptime(call["timestamp"], "%Y-%m-%d %H:%M:%S").strftime(
                        "%H:00"
                    )
                    call_volume[hour] = call_volume.get(hour, 0) + 1
                except:
                    continue

            call_volume_data = [
                {"name": hour, "calls": count} for hour, count in sorted(call_volume.items())
            ]
        else:
            total_calls_today = 0
            avg_duration = "N/A"
            call_volume_data = []

        return {
            "totalCalls": total_calls_today,
            "activeBookings": len(bookings),
            "avgCallDuration": avg_duration,
            "callVolume": call_volume_data,
        }
    except Exception as e:
        logger.exception("Error getting stats")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/settings")
async def get_settings(current_user: User = Depends(check_admin_role)):
    """Get current settings. Admin only."""
    try:
        with open("../../params.json") as f:
            params = json.load(f)

        # Get all environment variables
        settings = {}
        for key, env_key in ENV_MAPPING.items():
            value = os.getenv(env_key, "")
            if env_key == "RECORDING_ENABLED":
                settings[key] = value.lower() == "true"
            else:
                settings[key] = value

        # Add bot settings
        settings.update(
            {
                "welcomeMessage": params["discussion"]["welcome_message"],
                "assistantPrompt": params["prompts"]["assistant_prompt"],
                "enableInterruptions": True,
                "enableMetrics": True,
            }
        )

        return settings
    except Exception as e:
        logger.error(f"Error getting settings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/settings")
async def update_settings(settings: Settings, current_user: User = Depends(check_admin_role)):
    """Update settings. Admin only."""
    try:
        # Update environment variables
        for key, env_key in ENV_MAPPING.items():
            value = getattr(settings, key)
            if env_key == "RECORDING_ENABLED":
                value = str(value).lower()
            set_key(dotenv_path, env_key, str(value))
            os.environ[env_key] = str(value)

        # Update params.json
        with open("../../params.json", "r") as f:
            params = json.load(f)

        params["discussion"]["welcome_message"] = settings.welcomeMessage
        params["prompts"]["assistant_prompt"] = settings.assistantPrompt

        with open("../../params.json", "w") as f:
            json.dump(params, f, indent=2)

        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error updating settings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
