import json
import pytz
from datetime import datetime, timedelta
from loguru import logger
import aiohttp
from .airtable_config import AIRTABLE_API_KEY, AIRTABLE_BASE_ID, AIRTABLE_BOOKINGS_TABLE
from .utils import create_response, format_registration, format_date_for_display


async def find_booking(function_name, tool_call_id, arguments, llm, context, result_callback):
    registration = arguments.get("registration", "")

    if not registration:
        await result_callback(create_response(False, "Registration cannot be empty"))
        return

    logger.debug(f"Raw input - registration: {registration}")
    formatted_registration = format_registration(registration)
    logger.debug(f"Formatted registration: {formatted_registration}")

    url = (
        f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_BOOKINGS_TABLE}?"
        + f'filterByFormula=UPPER({{Registration}})=UPPER("{formatted_registration}")&'
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

                            # Format dates for display (MM/DD/YYYY)
                            display_start_date = format_date_for_display(record["Entry_Date_Time"])
                            display_end_date = format_date_for_display(record["Return_Date_Time"])

                            result = {
                                "found": True,
                                "expired": not is_active,
                                "is_drop_off": is_drop_off,
                                "customerName": record.get("Name", "Not provided"),
                                "terminal": record.get("Terminal", "Not provided"),
                                "startDate": display_start_date,
                                "endDate": display_end_date,
                                "contactNumber": record.get("Contact_Number", "Not provided"),
                                "allocatedCarPark": record.get(
                                    "Allocated_Car_Park", "Not provided"
                                ),
                                "registration": formatted_registration,
                                "vehicleMake": record.get("Vehicle_Make", "Not provided"),
                                "dropOffStatus": record.get("Drop_Off_Status", "Not Set"),
                                "collectionStatus": record.get("Collection_Status", "Not Set"),
                            }

                            await result_callback(create_response(True, "Booking found.", result))
                        except ValueError as e:
                            logger.error(f"Error parsing booking dates: {e}")
                            await result_callback(
                                create_response(False, f"Error parsing booking dates: {str(e)}")
                            )
                    else:
                        logger.warning(
                            f"No booking found for registration: {formatted_registration}"
                        )
                        await result_callback(
                            create_response(
                                False,
                                f"No booking found for registration {formatted_registration}.",
                            )
                        )
                else:
                    error_text = await response.text()
                    logger.error(f"Error response from Airtable: {response.status}")
                    await result_callback(
                        create_response(
                            False,
                            f"Failed to find booking. Status: {response.status}",
                            {"details": error_text},
                        )
                    )
        except Exception as error:
            logger.error(f"Error finding booking: {str(error)}")
            await result_callback(
                create_response(False, "Failed to find booking.", {"details": str(error)})
            )
