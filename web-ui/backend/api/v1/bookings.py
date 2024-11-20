from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import aiohttp
import pytz
from datetime import datetime, timedelta
import sys
import pathlib
from pathlib import Path
import os
from dotenv import load_dotenv
import json
from fastapi.encoders import jsonable_encoder

# Add backend directory to Python path
backend_dir = str(pathlib.Path(__file__).parent.parent.parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Add project root to Python path for functions module
project_root = str(pathlib.Path(__file__).parent.parent.parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

# Get Airtable configuration
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_BOOKINGS_TABLE = os.getenv("AIRTABLE_BOOKINGS_TABLE")

logger.info(f"Loaded Airtable configuration:")
logger.info(f"API Key present: {bool(AIRTABLE_API_KEY)}")
logger.info(f"Base ID present: {bool(AIRTABLE_BASE_ID)}")
logger.info(f"Table name present: {bool(AIRTABLE_BOOKINGS_TABLE)}")

from database import get_db, User
from auth import get_current_active_user, check_admin_role
from pydantic import BaseModel, Field, validator, ConfigDict

# Create the router
router = APIRouter(prefix="/bookings", tags=["bookings"])


def format_datetime(dt_str: Optional[str]) -> Optional[str]:
    """Format datetime string to a consistent format"""
    if not dt_str:
        return None
    try:
        # Try parsing the specific format used in Airtable
        dt = datetime.strptime(dt_str, "%d/%m/%Y %H:%M")
        return dt.strftime("%d/%m/%Y %H:%M")
    except ValueError:
        try:
            # Fallback to ISO format
            dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
            return dt.strftime("%d/%m/%Y %H:%M")
        except Exception as e:
            logger.error(f"Datetime parsing error for {dt_str}: {e}")
            return dt_str


class BookingModel(BaseModel):
    id: str
    bookingRef: str = Field(alias="Booking_Ref", default="")
    registration: str = Field(alias="Registration", default="")
    customerName: str = Field(alias="Name", default="")
    contactNumber: str = Field(alias="Contact_Number", default="")
    terminal: str = Field(alias="Terminal", default="")
    allocatedCarPark: str = Field(alias="Allocated_Car_Park", default="")
    dropOffStatus: str = Field(alias="Drop_Off_Status", default="")
    collectionStatus: str = Field(alias="Collection_Status", default="")
    entryDateTime: str = Field(alias="Entry_Date_Time", default="")
    returnDateTime: str = Field(alias="Return_Date_Time", default="")
    currentETA: Optional[str] = Field(alias="Current_ETA", default=None)
    outFlightNumber: str = Field(alias="Out_Flight_Number", default="")
    inFlightNumber: str = Field(alias="In_Flight_Number", default="")
    vehicleMake: str = Field(alias="Vehicle_Make", default="")
    productCode: str = Field(alias="Product_Code", default="")
    createdTime: str = Field(default="")

    model_config = {
        "populate_by_name": True,
        "json_encoders": {datetime: lambda v: v.strftime("%d/%m/%Y %H:%M") if v else None},
    }

    def dict(self, *args, **kwargs) -> Dict[str, Any]:
        # Override dict method to ensure proper serialization
        d = super().dict(*args, **kwargs)
        # Convert None values to empty strings for consistency
        return {k: "" if v is None else v for k, v in d.items()}


def map_airtable_to_booking(record: Dict[str, Any]) -> BookingModel:
    """Map Airtable record to BookingModel format"""
    logger.debug(f"Mapping record: {json.dumps(record, indent=2)}")

    fields = record.get("fields", {})

    booking_data = {
        "id": record.get("id", ""),
        "Booking_Ref": fields.get("Booking_Ref", ""),
        "Registration": fields.get("Registration", ""),
        "Name": fields.get("Name", ""),
        "Contact_Number": fields.get("Contact_Number", ""),
        "Terminal": fields.get("Terminal", ""),
        "Allocated_Car_Park": fields.get("Allocated_Car_Park", ""),
        "Drop_Off_Status": fields.get("Drop_Off_Status", ""),
        "Collection_Status": fields.get("Collection_Status", ""),
        "Entry_Date_Time": format_datetime(fields.get("Entry_Date_Time")),
        "Return_Date_Time": format_datetime(fields.get("Return_Date_Time")),
        "Current_ETA": format_datetime(fields.get("Current_ETA")),
        "Out_Flight_Number": fields.get("Out_Flight_Number", ""),
        "In_Flight_Number": fields.get("In_Flight_Number", ""),
        "Vehicle_Make": fields.get("Vehicle_Make", ""),
        "Product_Code": fields.get("Product_Code", ""),
        "createdTime": format_datetime(record.get("createdTime")),
    }

    return BookingModel(**booking_data)


def get_date_filter_formula(date_filter: Optional[str]) -> str:
    """Generate Airtable filter formula for date filtering"""
    if not date_filter:
        return ""

    # Use London timezone for consistency
    london_tz = pytz.timezone("Europe/London")
    today = datetime.now(london_tz).date()

    if date_filter == "today":
        start_date = today.strftime("%d/%m/%Y")
        end_date = today.strftime("%d/%m/%Y")
    elif date_filter == "yesterday":
        yesterday = today - timedelta(days=1)
        start_date = yesterday.strftime("%d/%m/%Y")
        end_date = yesterday.strftime("%d/%m/%Y")
    elif date_filter == "tomorrow":
        tomorrow = today + timedelta(days=1)
        start_date = tomorrow.strftime("%d/%m/%Y")
        end_date = tomorrow.strftime("%d/%m/%Y")
    else:
        return ""

    # Create a formula that checks if the entry or return date is within the specified date
    return (
        f"OR("
        f'FIND("{start_date}", LEFT({{Entry_Date_Time}}, 10)), '
        f'FIND("{start_date}", LEFT({{Return_Date_Time}}, 10))'
        f")"
    )


@router.get("")
async def get_bookings(
    current_user: User = Depends(get_current_active_user),
    status: Optional[str] = Query(None),
    terminal: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    date_filter: Optional[str] = Query(None),
):
    """
    Retrieve bookings from Airtable with optional filtering
    """
    logger.info(f"Received get_bookings request")
    logger.info(f"User: {current_user.username}")
    logger.info(
        f"Filters - status: {status}, terminal: {terminal}, search: {search}, date_filter: {date_filter}"
    )

    # Check Airtable configuration
    if not all([AIRTABLE_API_KEY, AIRTABLE_BASE_ID, AIRTABLE_BOOKINGS_TABLE]):
        logger.error("Missing Airtable configuration")
        logger.error(f"API Key present: {bool(AIRTABLE_API_KEY)}")
        logger.error(f"Base ID present: {bool(AIRTABLE_BASE_ID)}")
        logger.error(f"Table name present: {bool(AIRTABLE_BOOKINGS_TABLE)}")
        raise HTTPException(
            status_code=500,
            detail="Airtable configuration is missing. Please check your environment variables.",
        )

    # Build filter formula
    filter_parts = []
    if status:
        filter_parts.append(
            f'OR(FIND("{status}", {{Drop_Off_Status}}), FIND("{status}", {{Collection_Status}}))'
        )
    if terminal:
        filter_parts.append(f'{{Terminal}}="{terminal}"')
    if search:
        filter_parts.append(
            f'OR(FIND("{search}", {{Booking_Ref}}), '
            f'FIND("{search}", {{Registration}}), '
            f'FIND("{search}", {{Name}}))'
        )

    # Add date filter
    date_filter_formula = get_date_filter_formula(date_filter)
    if date_filter_formula:
        filter_parts.append(date_filter_formula)

    filter_formula = ""
    if filter_parts:
        filter_formula = "AND(" + ",".join(filter_parts) + ")"

    url = (
        f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_BOOKINGS_TABLE}?"
        + (f"filterByFormula={filter_formula}&" if filter_formula else "")
        + "cellFormat=string&timeZone=Europe/London&userLocale=en-gb"
    )

    headers = {"Authorization": f"Bearer {AIRTABLE_API_KEY}"}
    logger.info(f"Making Airtable request to: {url}")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                logger.info(f"Airtable response status: {response.status}")

                if response.status == 200:
                    data = await response.json()
                    logger.debug(f"Raw Airtable response: {json.dumps(data, indent=2)}")

                    # Filter out records with no fields
                    records = [record for record in data.get("records", []) if record.get("fields")]

                    bookings = [map_airtable_to_booking(record) for record in records]
                    logger.info(f"Found {len(bookings)} bookings")

                    # Convert to list of dicts and ensure proper JSON formatting
                    bookings_data = [booking.dict() for booking in bookings]

                    # Return using standard JSON response with proper formatting
                    return Response(
                        content=json.dumps(
                            bookings_data, indent=2, ensure_ascii=False, separators=(",", ": ")
                        ),
                        media_type="application/json",
                    )
                else:
                    error_text = await response.text()
                    logger.error(f"Airtable API error: {response.status} - {error_text}")
                    if response.status == 404:
                        raise HTTPException(
                            status_code=500,
                            detail="Airtable base or table not found. Please check your configuration.",
                        )
                    raise HTTPException(
                        status_code=500, detail=f"Failed to retrieve bookings: {error_text}"
                    )
    except aiohttp.ClientError as e:
        logger.error(f"Network error accessing Airtable: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Network error accessing Airtable: {str(e)}")
    except Exception as e:
        logger.error(f"Error retrieving bookings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving bookings: {str(e)}")


@router.put("/{booking_id}", response_model=BookingModel)
async def update_booking(
    booking_id: str,
    booking_data: BookingModel,
    current_user: User = Depends(get_current_active_user),
):
    """
    Update an existing booking in Airtable
    """
    # Check Airtable configuration
    if not all([AIRTABLE_API_KEY, AIRTABLE_BASE_ID, AIRTABLE_BOOKINGS_TABLE]):
        raise HTTPException(
            status_code=500,
            detail="Airtable configuration is missing. Please check your environment variables.",
        )

    logger.info(f"Updating booking {booking_id} for user: {current_user.username}")

    # Map booking data to Airtable fields
    fields = {
        "Booking_Ref": booking_data.bookingRef,
        "Registration": booking_data.registration,
        "Name": booking_data.customerName,
        "Contact_Number": booking_data.contactNumber,
        "Terminal": booking_data.terminal,
        "Allocated_Car_Park": booking_data.allocatedCarPark,
        "Drop_Off_Status": booking_data.dropOffStatus,
        "Collection_Status": booking_data.collectionStatus,
        "Entry_Date_Time": booking_data.entryDateTime,
        "Return_Date_Time": booking_data.returnDateTime,
        "Current_ETA": booking_data.currentETA,
        "Out_Flight_Number": booking_data.outFlightNumber,
        "In_Flight_Number": booking_data.inFlightNumber,
        "Vehicle_Make": booking_data.vehicleMake,
        "Product_Code": booking_data.productCode,
    }

    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_BOOKINGS_TABLE}/{booking_id}"
    headers = {"Authorization": f"Bearer {AIRTABLE_API_KEY}", "Content-Type": "application/json"}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.patch(url, headers=headers, json={"fields": fields}) as response:
                if response.status == 200:
                    data = await response.json()
                    return map_airtable_to_booking(data)
                else:
                    error_text = await response.text()
                    logger.error(f"Airtable API error: {response.status} - {error_text}")
                    if response.status == 404:
                        raise HTTPException(
                            status_code=500,
                            detail="Airtable base, table, or record not found. Please check your configuration.",
                        )
                    raise HTTPException(
                        status_code=500, detail=f"Failed to update booking: {error_text}"
                    )
    except aiohttp.ClientError as e:
        logger.error(f"Network error accessing Airtable: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Network error accessing Airtable: {str(e)}")
    except Exception as e:
        logger.error(f"Error updating booking: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating booking: {str(e)}")
