import json
import pytz
from datetime import datetime
from loguru import logger
import aiohttp
import re
from .airtable_config import AIRTABLE_API_KEY, AIRTABLE_BASE_ID, AIRTABLE_BOOKINGS_TABLE
from .utils import create_response, format_registration


def clean_phone_number(phone_number):
    if not phone_number:
        return None

    # Remove all non-digit characters
    cleaned_number = re.sub(r"\D", "", phone_number)

    # Handle international format
    if cleaned_number.startswith("44"):
        cleaned_number = "0" + cleaned_number[2:]
    elif not cleaned_number.startswith("0"):
        cleaned_number = "0" + cleaned_number

    # Validate length for UK numbers (should be 11 digits)
    if len(cleaned_number) != 11:
        logger.warning(f"Invalid phone number length: {cleaned_number}")
        return None

    return cleaned_number


async def update_phone_number(
    function_name, tool_call_id, arguments, llm, context, result_callback
):
    registration = arguments.get("registration")
    phone_number = arguments.get("phone_number")

    # Clean the phone number
    cleaned_phone_number = clean_phone_number(phone_number)
    if not cleaned_phone_number:
        await result_callback(create_response(False, "Invalid phone number format"))
        return

    timezone = pytz.timezone("Europe/London")
    current_time = datetime.now(timezone)
    logger.debug(
        f"Updating phone number for registration: {registration}, new number: {cleaned_phone_number}, currentTime: {current_time.strftime('%Y-%m-%d %H:%M:%S')}"
    )

    formatted_registration = format_registration(registration)

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
                            create_response(False, "No booking found for this registration number.")
                        )
                        return

                    record = data["records"][0]
                    record_id = record["id"]

                    patch_url = (
                        f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_BOOKINGS_TABLE}"
                    )
                    patch_data = {
                        "records": [
                            {"id": record_id, "fields": {"Contact_Number": cleaned_phone_number}}
                        ],
                        "typecast": True,
                    }

                    async with session.patch(
                        patch_url, headers=headers, json=patch_data
                    ) as patch_response:
                        if patch_response.status == 200:
                            patch_data = await patch_response.json()
                            logger.info(
                                f"Phone number updated successfully. New number: {cleaned_phone_number}"
                            )
                            await result_callback(
                                create_response(
                                    True,
                                    "Phone number updated successfully.",
                                    {
                                        "updatedRecord": patch_data["records"][0],
                                        "updatedPhoneNumber": cleaned_phone_number,
                                    },
                                )
                            )
                        else:
                            error_text = await patch_response.text()
                            logger.error(f"Error updating phone number: {error_text}")
                            await result_callback(
                                create_response(
                                    False, "Failed to update phone number.", {"details": error_text}
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
            logger.error(f"Error updating phone number: {str(error)}")
            await result_callback(
                create_response(False, "Failed to update phone number.", {"details": str(error)})
            )
