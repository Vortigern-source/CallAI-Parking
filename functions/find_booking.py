import json
import pytz
from datetime import datetime
from loguru import logger
import aiohttp
from .airtable_config import AIRTABLE_API_KEY, AIRTABLE_BASE_ID, AIRTABLE_BOOKINGS_TABLE


async def find_booking(function_name, tool_call_id, arguments, llm, context, result_callback):
    registration = arguments.get("registration", "")
    is_arrival = arguments.get("is_arrival", False)

    logger.debug(f"Raw input - registration: {registration}, isArrival: {is_arrival}")

    # Remove any non-alphanumeric characters and convert to uppercase
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
                            booking_time = datetime.strptime(
                                record["Entry_Date_Time"], "%d/%m/%Y %H:%M"
                            )
                            booking_time = pytz.timezone("Europe/London").localize(booking_time)
                            formatted_booking_time = booking_time.strftime("%B %d at %I:%M %p")
                        except ValueError:
                            logger.error(f"Error parsing booking time: {record['Entry_Date_Time']}")
                            formatted_booking_time = "Date format error"
                        contact_number = record.get("Contact_Number", "Not provided")
                        if contact_number != "Not provided":
                            contact_number = " ".join(
                                [
                                    contact_number[i : i + 4]
                                    for i in range(0, len(contact_number), 4)
                                ]
                            )

                        customer_name = record.get("Name", "Not provided")
                        terminal = record.get("Terminal", "Not provided")
                        allocated_car_park = record.get("Allocated_Car_Park", "Not provided")

                        result = {
                            "found": True,
                            "customerName": customer_name,
                            "terminal": terminal,
                            "bookingTime": formatted_booking_time,
                            "contactNumber": contact_number,
                            "allocatedCarPark": allocated_car_park,
                            "registration": formatted_registration,
                        }

                        await result_callback(json.dumps(result))
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
                elif response.status == 404:
                    logger.warning(f"No booking found for registration: {formatted_registration}")
                    await result_callback(json.dumps({"error": "Booking not found"}))
                elif response.status == 401:
                    logger.error("Unauthorized access to Airtable API")
                    await result_callback(json.dumps({"error": "Authentication failed"}))
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
