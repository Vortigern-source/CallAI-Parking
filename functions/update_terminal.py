import json
import pytz
from datetime import datetime
from loguru import logger
import aiohttp
from .airtable_config import AIRTABLE_API_KEY, AIRTABLE_BASE_ID, AIRTABLE_BOOKINGS_TABLE


async def update_terminal(function_name, tool_call_id, arguments, llm, context, result_callback):
    registration = arguments.get("registration")
    terminal = arguments.get("terminal")

    # Format the terminal input
    formatted_terminal = terminal.strip()
    if not formatted_terminal.lower().startswith("terminal"):
        formatted_terminal = f"Terminal {formatted_terminal}"
    formatted_terminal = formatted_terminal.title()

    timezone = pytz.timezone("Europe/London")
    current_time = datetime.now(timezone)
    logger.debug(
        f"Updating terminal for registration: {registration}, new terminal: {formatted_terminal}, currentTime: {current_time.strftime('%Y-%m-%d %H:%M:%S')}"
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

                    patch_url = (
                        f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_BOOKINGS_TABLE}"
                    )
                    patch_data = {
                        "records": [{"id": record_id, "fields": {"Terminal": formatted_terminal}}],
                        "typecast": True,
                    }

                    async with session.patch(
                        patch_url, headers=headers, json=patch_data
                    ) as patch_response:
                        if patch_response.status == 200:
                            patch_data = await patch_response.json()
                            logger.info(f"Terminal updated successfully. New terminal: {terminal}")
                            await result_callback(
                                json.dumps(
                                    {
                                        "success": "Terminal updated successfully.",
                                        "updatedRecord": patch_data["records"][0],
                                        "updatedTerminal": terminal,
                                    }
                                )
                            )
                        else:
                            error_text = await patch_response.text()
                            logger.error(f"Error updating terminal: {error_text}")
                            await result_callback(
                                json.dumps(
                                    {"error": "Failed to update terminal.", "details": error_text}
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
            logger.error(f"Error updating terminal: {str(error)}")
            await result_callback(
                json.dumps({"error": "Failed to update terminal.", "details": str(error)})
            )
