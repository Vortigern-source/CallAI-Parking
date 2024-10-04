import pytz
from datetime import datetime, timedelta
import re
import json


def get_current_time():
    utc_now = datetime.now(pytz.utc)
    uk_tz = pytz.timezone("Europe/London")
    uk_time = utc_now.astimezone(uk_tz)
    formatted_time = uk_time.strftime("%I:%M %p")
    return {"current_time": formatted_time, "timestamp": uk_time.isoformat()}


async def handle_get_current_time(
    function_name, tool_call_id, arguments, llm, context, result_callback
):
    current_time_info = get_current_time()
    await result_callback(json.dumps(current_time_info))


def get_current_date():
    utc_now = datetime.now(pytz.utc)
    uk_tz = pytz.timezone("Europe/London")
    uk_date = utc_now.astimezone(uk_tz)
    formatted_date = uk_date.strftime("%d/%m/%Y")
    return {"current_date": formatted_date, "timestamp": uk_date.isoformat()}


async def handle_get_current_date(
    function_name, tool_call_id, arguments, llm, context, result_callback
):
    current_date_info = get_current_date()
    await result_callback(json.dumps(current_date_info))


def parse_eta(eta_string, current_time, timezone):
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
