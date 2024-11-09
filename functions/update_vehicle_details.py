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
    vehicle_make = arguments.get("vehicle_make")
    vehicle_model = arguments.get("vehicle_make")  # Updated to use "vehicle_make"

    timezone = pytz.timezone("Europe/London")
    current_time = datetime.now(timezone)
    logger.debug(
        f"Updating vehicle details for registration: {registration}, new vehicle make: {vehicle_make}, new vehicle model: {vehicle_model}, currentTime: {current_time.strftime('%Y-%m-%d %H:%M:%S')}"
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
                    current_vehicle_make = record["fields"].get("Vehicle_Make")
                    current_vehicle_model = record["fields"].get(
                        "Vehicle_Make"
                    )  # Updated to use "Vehicle_Make"

                    # Store both old and new vehicle details for comparison
                    fields = {"Vehicle_Make": vehicle_make}  # Removed "Vehicle_Model"

                    patch_url = (
                        f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_BOOKINGS_TABLE}"
                    )
                    patch_data = {
                        "records": [{"id": record_id, "fields": fields}],
                        "typecast": True,
                    }

                    async with session.patch(
                        patch_url, headers=headers, json=patch_data
                    ) as patch_response:
                        if patch_response.status == 200:
                            patch_data = await patch_response.json()
                            logger.info(
                                f"Vehicle details updated successfully. New vehicle make: {vehicle_make}"
                            )
                            # Return both old and new vehicle details
                            response = create_response(
                                True,
                                "Vehicle details updated successfully.",
                                {
                                    "oldVehicleMake": current_vehicle_make,
                                    "oldVehicleModel": current_vehicle_model,
                                    "updatedVehicleMake": vehicle_make,
                                    "updatedVehicleModel": vehicle_model,
                                    "updatedRecord": patch_data["records"][0],
                                },
                            )
                            logger.debug(f"Response data: {response}")
                            await result_callback(response)
                            return response
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
