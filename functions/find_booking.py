import json
import pytz
from datetime import datetime, timedelta
from loguru import logger
import aiohttp
from .airtable_config import AIRTABLE_API_KEY, AIRTABLE_BASE_ID, AIRTABLE_BOOKINGS_TABLE
from .whatsapp_message import whatsapp_message_extension


def convert_to_12hour(time_str):
    time_obj = datetime.strptime(time_str, "%H:%M")
    return time_obj.strftime("%I:%M %p")


def format_date(date_str, input_format="%d/%m/%Y %H:%M", output_format="%m/%d/%Y %I:%M %p"):
    """Convert date string from one format to another"""
    try:
        date_obj = datetime.strptime(date_str, input_format)
        return date_obj.strftime(output_format)
    except ValueError:
        return date_str


async def find_booking(function_name, tool_call_id, arguments, llm, context, result_callback):
    registration = arguments.get("registration", "")

    logger.debug(f"Raw input - registration: {registration}")

    formatted_registration = "".join(char for char in registration if char.isalnum()).upper()

    logger.debug(f"Formatted registration: {formatted_registration}")

    table_name = AIRTABLE_BOOKINGS_TABLE

    url = (
        f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{table_name}?"
        + f'filterByFormula=UPPER({{Registration}})="{formatted_registration}"&'
        + "cellFormat=string&timeZone=Europe/London&userLocale=en-gb"
    )

    headers = {"Authorization": f"Bearer {AIRTABLE_API_KEY}"}

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    if data["records"]:
                        record = data["records"][0]["fields"]
                        try:
                            start_date = datetime.strptime(
                                record["Entry_Date_Time"], "%d/%m/%Y %H:%M"
                            )
                            start_date = pytz.timezone("Europe/London").localize(start_date)
                            end_date = datetime.strptime(
                                record["Return_Date_Time"], "%d/%m/%Y %H:%M"
                            )
                            end_date = pytz.timezone("Europe/London").localize(end_date)
                            current_time = datetime.now(pytz.timezone("Europe/London"))

                            is_drop_off = current_time < end_date
                            is_active = (
                                is_drop_off
                                and start_date - timedelta(hours=24) <= current_time <= end_date
                            ) or (
                                not is_drop_off
                                and start_date <= current_time <= end_date + timedelta(hours=24)
                            )

                            result = {
                                "found": True,
                                "expired": not is_active,
                                "is_drop_off": is_drop_off,
                                "customerName": record.get("Name", "Not provided"),
                                "terminal": record.get("Terminal", "Not provided"),
                                "startDate": format_date(start_date.strftime("%d/%m/%Y %H:%M")),
                                "endDate": format_date(end_date.strftime("%d/%m/%Y %H:%M")),
                                "contactNumber": record.get("Contact_Number", "Not provided"),
                                "allocatedCarPark": record.get(
                                    "Allocated_Car_Park", "Not provided"
                                ),
                                "registration": formatted_registration,
                                "vehicleMake": record.get("Vehicle_Make", "Not provided"),
                                "dropOffStatus": record.get("Drop_Off_Status", "Not Set"),
                                "collectionStatus": record.get("Collection_Status", "Not Set"),
                            }

                            await result_callback(json.dumps(result))
                        except ValueError as e:
                            logger.error(f"Error parsing booking dates: {e}")
                            await result_callback(
                                json.dumps({"error": f"Error parsing booking dates: {str(e)}"})
                            )
                    else:
                        logger.warning(
                            f"No booking found for registration: {formatted_registration}"
                        )
                        await result_callback(
                            json.dumps(
                                {
                                    "found": False,
                                    "error": f"No booking found for registration {formatted_registration}.",
                                }
                            )
                        )
                else:
                    logger.error(f"Error response from Airtable: {response.status}")
                    await result_callback(
                        json.dumps(
                            {
                                "found": False,
                                "error": f"Failed to find booking. Status: {response.status}",
                            }
                        )
                    )
        except Exception as error:
            logger.error(f"Error finding booking: {str(error)}")
            await result_callback(
                json.dumps(
                    {"found": False, "error": f"Failed to find booking. Error: {str(error)}"}
                )
            )
