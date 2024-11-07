import json
import pytz
from datetime import datetime
from loguru import logger
import aiohttp
from .airtable_config import AIRTABLE_API_KEY, AIRTABLE_BASE_ID, AIRTABLE_BOOKINGS_TABLE
from .utils import (
    create_response,
    format_registration,
    format_date_for_display,
    format_date_for_airtable,
    parse_eta,
    get_uk_timezone,
)


async def update_eta(function_name, tool_call_id, arguments, llm, context, result_callback):
    """Update the ETA for a booking"""
    customer_eta = arguments.get("customer_eta")
    registration = arguments.get("registration")

    if not customer_eta:
        await result_callback(create_response(False, "ETA cannot be empty"))
        return

    timezone = get_uk_timezone()
    current_time = datetime.now(timezone)

    # Format the registration number
    formatted_registration = format_registration(registration)

    logger.debug(
        f"Updating ETA for registration: {formatted_registration}, customerETA: {customer_eta}, currentTime: {current_time.strftime('%Y-%m-%d %H:%M:%S')}"
    )

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

                    # Parse ETA
                    parsed_eta = parse_eta(customer_eta, current_time, timezone)

                    # Handle special case for collections
                    if customer_eta.lower() == "customer has collected luggage":
                        formatted_eta = customer_eta
                        display_eta = customer_eta
                    else:
                        if parsed_eta is None:
                            logger.error(f"Invalid ETA format: {customer_eta}")
                            await result_callback(
                                create_response(
                                    False,
                                    "Invalid ETA format. Please provide a time like '30 minutes', '2 hours', or '4:30 PM'.",
                                )
                            )
                            return

                        if isinstance(parsed_eta, datetime) and parsed_eta < current_time:
                            logger.error(f"ETA cannot be in the past: {customer_eta}")
                            await result_callback(
                                create_response(False, "ETA cannot be in the past.")
                            )
                            return

                        # Format ETA for Airtable storage (DD/MM/YYYY)
                        formatted_eta = format_date_for_airtable(parsed_eta)
                        # Format ETA for display/TTS (MM/DD/YYYY)
                        display_eta = format_date_for_display(formatted_eta)

                    # Update Airtable
                    patch_url = (
                        f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_BOOKINGS_TABLE}"
                    )
                    patch_data = {
                        "records": [{"id": record_id, "fields": {"Current_ETA": formatted_eta}}],
                        "typecast": True,
                    }

                    async with session.patch(
                        patch_url, headers=headers, json=patch_data
                    ) as patch_response:
                        if patch_response.status == 200:
                            patch_data = await patch_response.json()
                            logger.info(f"ETA updated successfully. New ETA: {formatted_eta}")

                            await result_callback(
                                create_response(
                                    True,
                                    "ETA updated successfully.",
                                    {
                                        "updatedRecord": patch_data["records"][0],
                                        "updatedETA": display_eta,
                                    },
                                )
                            )
                        else:
                            error_text = await patch_response.text()
                            logger.error(f"Error updating ETA: {error_text}")
                            await result_callback(
                                create_response(
                                    False, "Failed to update ETA.", {"details": error_text}
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
            logger.error(f"Error updating ETA: {str(error)}")
            await result_callback(
                create_response(False, "Failed to update ETA.", {"details": str(error)})
            )
