import json
import pytz
from datetime import datetime
from loguru import logger
import aiohttp
from .airtable_config import AIRTABLE_API_KEY, AIRTABLE_BASE_ID, AIRTABLE_BOOKINGS_TABLE
from .utils import create_response, format_registration


async def update_vehicle_details(
    function_name, tool_call_id, arguments, llm, context, result_callback
):
    registration = arguments.get("registration")
    vehicle_details = arguments.get("vehicle_details")

    if not vehicle_details:
        await result_callback(create_response(False, "Vehicle details cannot be empty"))
        return

    timezone = pytz.timezone("Europe/London")
    current_time = datetime.now(timezone)
    logger.debug(
        f"Updating vehicle details for registration: {registration}, new details: {vehicle_details}, currentTime: {current_time.strftime('%Y-%m-%d %H:%M:%S')}"
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
                        "records": [{"id": record_id, "fields": {"Vehicle_Make": vehicle_details}}],
                        "typecast": True,
                    }

                    async with session.patch(
                        patch_url, headers=headers, json=patch_data
                    ) as patch_response:
                        if patch_response.status == 200:
                            patch_data = await patch_response.json()
                            logger.info(
                                f"Vehicle details updated successfully. New details: {vehicle_details}"
                            )
                            await result_callback(
                                create_response(
                                    True,
                                    "Vehicle details updated successfully.",
                                    {
                                        "updatedRecord": patch_data["records"][0],
                                        "updatedVehicleDetails": vehicle_details,
                                    },
                                )
                            )
                        else:
                            error_text = await patch_response.text()
                            logger.error(f"Error updating vehicle details: {error_text}")
                            await result_callback(
                                create_response(
                                    False,
                                    "Failed to update vehicle details.",
                                    {"details": error_text},
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
            logger.error(f"Error updating vehicle details: {str(error)}")
            await result_callback(
                create_response(False, "Failed to update vehicle details.", {"details": str(error)})
            )
