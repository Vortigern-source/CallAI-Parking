import json
import pytz
import re
from datetime import datetime
from loguru import logger
import aiohttp
from .airtable_config import AIRTABLE_API_KEY, AIRTABLE_BASE_ID, AIRTABLE_BOOKINGS_TABLE


async def find_booking_by_phone(
    function_name, tool_call_id, arguments, llm, context, result_callback
):
    phone_number = arguments.get("phone_number")

    logger.debug(f"Finding booking for phone number: {phone_number}")

    # Remove any non-digit characters and ensure the number starts with '44' or '0'
    formatted_phone_number = re.sub(r"\D", "", phone_number)
    if formatted_phone_number.startswith("44"):
        formatted_phone_number = "0" + formatted_phone_number[2:]
    elif not formatted_phone_number.startswith("0"):
        formatted_phone_number = "0" + formatted_phone_number

    url = (
        f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_BOOKINGS_TABLE}?"
        f'filterByFormula=OR(SEARCH("{formatted_phone_number}",{{Contact_Number}}),SEARCH("{formatted_phone_number.replace("^0", "44")}",{{Contact_Number}}))&'
        f"cellFormat=string&timeZone=Europe/London&userLocale=en-gb"
    )

    headers = {"Authorization": f"Bearer {AIRTABLE_API_KEY}"}

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    if data["records"]:
                        record = data["records"][0]["fields"]
                        # Process and return the booking information
                        # You may want to adjust this part based on your specific needs
                        result = {
                            "found": True,
                            "booking": record,
                        }
                        await result_callback(json.dumps(result))
                    else:
                        logger.warning(
                            f"No booking found for phone number: {formatted_phone_number}"
                        )
                        await result_callback(
                            json.dumps(
                                {
                                    "found": False,
                                    "error": f"No booking found for phone number {formatted_phone_number}.",
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
            logger.error(f"Error finding booking by phone: {str(error)}")
            await result_callback(
                json.dumps(
                    {"found": False, "error": f"Failed to find booking. Error: {str(error)}"}
                )
            )
