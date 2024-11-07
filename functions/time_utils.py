import pytz
from datetime import datetime, timedelta
import re
from .utils import create_response


def get_current_time():
    """Get current time in UK timezone formatted for TTS (HH:MM AM/PM)"""
    utc_now = datetime.now(pytz.utc)
    uk_tz = pytz.timezone("Europe/London")
    uk_time = utc_now.astimezone(uk_tz)
    formatted_time = uk_time.strftime("%I:%M %p")
    return {"current_time": formatted_time, "timestamp": uk_time.isoformat()}


async def handle_get_current_time(
    function_name, tool_call_id, arguments, llm, context, result_callback
):
    """Handle getting current time in UK timezone"""
    try:
        current_time_info = get_current_time()
        await result_callback(create_response(True, "Current time retrieved.", current_time_info))
    except Exception as error:
        await result_callback(
            create_response(False, "Failed to get current time.", {"details": str(error)})
        )


def get_current_date():
    """Get current date in UK timezone formatted for TTS (MM/DD/YYYY)"""
    utc_now = datetime.now(pytz.utc)
    uk_tz = pytz.timezone("Europe/London")
    uk_date = utc_now.astimezone(uk_tz)
    formatted_date = uk_date.strftime("%m/%d/%Y")
    return {"current_date": formatted_date, "timestamp": uk_date.isoformat()}


async def handle_get_current_date(
    function_name, tool_call_id, arguments, llm, context, result_callback
):
    """Handle getting current date in UK timezone"""
    try:
        current_date_info = get_current_date()
        await result_callback(create_response(True, "Current date retrieved.", current_date_info))
    except Exception as error:
        await result_callback(
            create_response(False, "Failed to get current date.", {"details": str(error)})
        )


# Note: parse_eta has been moved to utils.py to avoid duplication
# and maintain consistency across the application
