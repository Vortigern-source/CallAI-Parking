import json
import pytz
import re
from datetime import datetime, timedelta
from loguru import logger
import aiohttp
from .airtable_config import AIRTABLE_API_KEY, AIRTABLE_BASE_ID, AIRTABLE_BOOKINGS_TABLE


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


async def update_eta(function_name, tool_call_id, arguments, llm, context, result_callback):
    customer_eta = arguments.get("customer_eta")
    registration = arguments.get("registration")

    timezone = pytz.timezone("Europe/London")
    current_time = datetime.now(timezone)
    logger.debug(
        f"Updating ETA for registration: {registration}, customerETA: {customer_eta}, currentTime: {current_time.strftime('%Y-%m-%d %H:%M:%S')}"
    )

    formatted_registration = registration.replace(" ", "").upper()

    url = (
        f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_BOOKINGS_TABLE}?"
        f'filterByFormula=UPPER({{Registration}})=UPPER("{formatted_registration}")&'
        f"cellFormat=string&timeZone=Europe/London&userLocale=en-gb"
    )

    headers = {"Authorization": f"Bearer {AIRTABLE_API_KEY}"}

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    if not data["records"]:
                        logger.warning(
                            f"No booking found for registration: {formatted_registration}"
                        )
                        await result_callback(
                            json.dumps({"error": "No booking found for this registration number."})
                        )
                        return

                    record = data["records"][0]
                    record_id = record["id"]

                    parsed_eta = parse_eta(customer_eta, current_time, timezone)
                    if parsed_eta is None:
                        logger.error(f"Invalid ETA format: {customer_eta}")
                        await result_callback(json.dumps({"error": "Invalid ETA format."}))
                        return

                    patch_url = (
                        f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_BOOKINGS_TABLE}"
                    )
                    patch_data = {
                        "records": [
                            {
                                "id": record_id,
                                "fields": {"Current_ETA": parsed_eta.strftime("%Y-%m-%d %H:%M:%S")},
                            }
                        ],
                        "typecast": True,
                    }

                    async with session.patch(
                        patch_url, headers=headers, json=patch_data
                    ) as patch_response:
                        if patch_response.status == 200:
                            patch_data = await patch_response.json()
                            logger.info(
                                f"ETA updated successfully. New ETA: {parsed_eta.strftime('%Y-%m-%d %H:%M:%S')}"
                            )
                            await result_callback(
                                json.dumps(
                                    {
                                        "success": "ETA updated successfully.",
                                        "updatedRecord": patch_data["records"][0],
                                        "updatedETA": parsed_eta.strftime("%Y-%m-%d %H:%M:%S"),
                                    }
                                )
                            )
                        else:
                            error_text = await patch_response.text()
                            logger.error(f"Error updating ETA: {error_text}")
                            await result_callback(
                                json.dumps(
                                    {"error": "Failed to update ETA.", "details": error_text}
                                )
                            )
                else:
                    error_text = await response.text()
                    logger.error(f"Error response from Airtable: {response.status}")
                    await result_callback(
                        json.dumps(
                            {
                                "error": f"Failed to find booking. Status: {response.status}",
                                "details": error_text,
                            }
                        )
                    )
        except Exception as error:
            logger.error(f"Error updating ETA: {str(error)}")
            await result_callback(
                json.dumps({"error": "Failed to update ETA.", "details": str(error)})
            )
