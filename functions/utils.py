from typing import Dict, Any, Optional
import json
import re
from datetime import datetime, timedelta
import pytz


def create_response(success: bool, message: str, additional_data: dict = None) -> str:
    """Create a standardized JSON response"""
    response = {"success" if success else "error": message}
    if additional_data:
        response.update(additional_data)
    return json.dumps(response)


def format_registration(registration: str) -> str:
    """
    Formats a vehicle registration number by removing special characters and spaces,
    and converting to uppercase.

    Args:
        registration (str): The registration number to format

    Returns:
        str: The formatted registration number
    """
    if not registration:
        return ""
    # Remove all non-alphanumeric characters and convert to uppercase
    return "".join(char for char in registration if char.isalnum()).upper()


def validate_required_args(arguments: dict, required_fields: list) -> None:
    """Validate required arguments"""
    missing = [field for field in required_fields if not arguments.get(field)]
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")


def format_date_for_display(date_str: str, input_format: str = "%d/%m/%Y %H:%M") -> str:
    """
    Format date for display/TTS in MM/DD/YYYY format.
    Input date should be in DD/MM/YYYY format (Airtable format).

    Args:
        date_str: Date string in DD/MM/YYYY format
        input_format: Format of the input date string, defaults to "%d/%m/%Y %H:%M"

    Returns:
        str: Date formatted as MM/DD/YYYY HH:MM AM/PM for display/TTS
    """
    try:
        date_obj = datetime.strptime(date_str, input_format)
        return date_obj.strftime("%m/%d/%Y %I:%M %p")
    except ValueError:
        return date_str


def format_date_for_airtable(date_obj: datetime) -> str:
    """
    Format datetime object for storage in Airtable in DD/MM/YYYY format.

    Args:
        date_obj: datetime object to format

    Returns:
        str: Date formatted as DD/MM/YYYY HH:MM for Airtable storage
    """
    return date_obj.strftime("%d/%m/%Y %H:%M")


def format_phone_for_display(phone: str) -> str:
    """
    Format phone number with dashes for display/TTS.
    Example: 07984334455 -> 0798-4334-455

    Args:
        phone: Phone number to format

    Returns:
        str: Phone number with dashes for display
    """
    if not phone:
        return "N/A"
    # Remove all non-digit characters
    cleaned = re.sub(r"\D", "", str(phone))
    # Handle UK format (11 digits starting with 0)
    if len(cleaned) == 11 and cleaned.startswith("0"):
        return f"{cleaned[:4]}-{cleaned[4:8]}-{cleaned[8:]}"
    # Handle international format (remove 44 prefix)
    elif len(cleaned) == 12 and cleaned.startswith("44"):
        cleaned = "0" + cleaned[2:]
        return f"{cleaned[:4]}-{cleaned[4:8]}-{cleaned[8:]}"
    return phone  # Return original if not in expected format


def format_registration_for_display(reg: str) -> str:
    """
    Format registration with dashes for display/TTS.
    Example: RJ23VMO -> R-J-2-3-V-M-O

    Args:
        reg: Registration to format

    Returns:
        str: Registration with dashes for display
    """
    if not reg:
        return "N/A"
    # Remove any existing formatting and convert to uppercase
    cleaned = format_registration(reg)
    return "-".join(cleaned)


def parse_eta(eta_string: str, current_time: datetime, timezone) -> Optional[datetime]:
    """
    Parse ETA string into datetime object. Handles relative times (e.g., "30 minutes")
    and absolute times (e.g., "4:30 PM" or "16:30").

    Args:
        eta_string: String containing the ETA
        current_time: Current datetime for relative time calculations
        timezone: Timezone to use for the result

    Returns:
        datetime: Parsed datetime object, or None if parsing fails
    """
    relative_regex = r"(\d+)\s*(minutes?|hours?)"
    match = re.match(relative_regex, eta_string, re.IGNORECASE)
    if match:
        value = int(match.group(1))
        unit = "hours" if match.group(2).lower().startswith("hour") else "minutes"
        return current_time + timedelta(**{unit: value})

    try:
        parsed_time = datetime.strptime(eta_string, "%I:%M %p").time()
        eta_datetime = datetime.combine(current_time.date(), parsed_time)
        if parsed_time < current_time.time():
            eta_datetime += timedelta(days=1)
        return timezone.localize(eta_datetime)
    except ValueError:
        pass

    try:
        parsed_time = datetime.strptime(eta_string, "%H:%M").time()
        eta_datetime = datetime.combine(current_time.date(), parsed_time)
        if parsed_time < current_time.time():
            eta_datetime += timedelta(days=1)
        return timezone.localize(eta_datetime)
    except ValueError:
        pass

    return None


def get_uk_timezone():
    """Get the UK timezone"""
    return pytz.timezone("Europe/London")
