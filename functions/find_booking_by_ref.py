import json
import pytz
from datetime import datetime, timedelta
from loguru import logger
import aiohttp
from .airtable_config import AIRTABLE_API_KEY, AIRTABLE_BASE_ID, AIRTABLE_BOOKINGS_TABLE


async def find_booking_by_ref(function_name, tool_call_id, arguments, llm, context, result_callback):
    booking_ref = arguments.get("booking_ref", "")

    logger.debug(f"Looking up booking with reference: {booking_ref}")

    # Format booking reference to match Airtable format (uppercase)
    formatted_booking_ref = booking_ref.strip().upper()

    url = (
        f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_BOOKINGS_TABLE}?"
        + f'filterByFormula=UPPER({{Booking_Ref}})="{formatted_booking_ref}"&'
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
                                "startDate": start_date.strftime("%m/%d/%Y %I:%M %p"),
                                "endDate": end_date.strftime("%m/%d/%Y %I:%M %p"),
                                "contactNumber": record.get("Contact_Number", "Not provided"),
                                "allocatedCarPark": record.get(
                                    "Allocated_Car_Park", "Not provided"
                                ),
                                "registration": record.get("Registration", "Not provided"),
                                "vehicleMake": record.get("Vehicle_Make", "Not provided"),
                                "dropOffStatus": record.get("Drop_Off_Status", "Not Set"),
                                "collectionStatus": record.get("Collection_Status", "Not Set"),
                                "bookingRef": formatted_booking_ref
                            }

                            await result_callback(json.dumps(result))
                        except ValueError as e:
                            logger.error(f"Error parsing booking dates: {e}")
                            await result_callback(
                                json.dumps({"error": f"Error parsing booking dates: {str(e)}"})
                            )
                    else:
                        logger.warning(f"No booking found for reference: {formatted_booking_ref}")
                        await result_callback(
                            json.dumps(
                                {
                                    "found": False,
                                    "error": f"No booking found for reference {formatted_booking_ref}.",
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