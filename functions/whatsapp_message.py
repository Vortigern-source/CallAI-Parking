import os
import json
import aiohttp
from urllib.parse import urlencode
from loguru import logger
from .airtable_config import (
    AIRTABLE_API_KEY,
    AIRTABLE_BASE_ID,
    AIRTABLE_BOOKINGS_TABLE,
)


async def whatsapp_message(function_name, tool_call_id, arguments, llm, context, result_callback):
    registration = arguments.get("registration")
    is_arrival = arguments.get("is_arrival", False)

    table_name = AIRTABLE_BOOKINGS_TABLE
    twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    twilio_whatsapp_number = os.getenv("TWILIO_WHATSAPP_NUMBER")
    manager_whatsapp_group = os.getenv("MANAGER_WHATSAPP_GROUP")

    formatted_registration = registration.replace(" ", "").upper()

    airtable_url = (
        f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{table_name}?"
        f'filterByFormula=UPPER({{Registration}})=UPPER("{formatted_registration}")&'
        f"cellFormat=string&timeZone=Europe/London&userLocale=en-gb"
    )

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(
                airtable_url, headers={"Authorization": f"Bearer {AIRTABLE_API_KEY}"}
            ) as response:
                airtable_data = await response.json()

            if airtable_data["records"]:
                record = airtable_data["records"][0]["fields"]

                vehicle_make = record.get("Vehicle_Make", "N/A")
                name = record.get("Name", "N/A")
                contact_number = record.get("Contact_Number", "N/A")
                entry_date_time = record.get("Entry_Date_Time", "N/A")
                terminal = record.get("Terminal", "N/A")
                estimated_eta = record.get("Current_ETA", "N/A")

                booking_type = "Arrival (Pick-up)" if is_arrival else "(Drop-off)"

                message = f"""
New {booking_type} Booking Requires Driver Assignment:
- Vehicle: {vehicle_make}
- Registration: {registration}
- Customer Name: {name}
- Contact Number: {contact_number}
- {"Arrival" if is_arrival else "Entry"} Date/Time: {entry_date_time}
- Estimated {"Landing Time" if is_arrival else "ETA"}: {estimated_eta}
- Terminal: {terminal}

Please assign a driver for this {"pick-up" if is_arrival else "drop-off"}.
"""

                logger.debug(f"WhatsApp message content: {message}")

                twilio_url = (
                    f"https://api.twilio.com/2010-04-01/Accounts/{twilio_account_sid}/Messages.json"
                )
                auth = aiohttp.BasicAuth(twilio_account_sid, twilio_auth_token)
                data = {
                    "From": f"whatsapp:{twilio_whatsapp_number}",
                    "To": f"whatsapp:{manager_whatsapp_group}",
                    "Body": message,
                }

                async with session.post(
                    twilio_url,
                    auth=auth,
                    data=urlencode(data),
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                ) as twilio_response:
                    twilio_data = await twilio_response.json()

                if twilio_response.status == 201:
                    if "sid" in twilio_data:
                        logger.info(f'WhatsApp message sent successfully: {twilio_data["sid"]}')
                        await result_callback(
                            json.dumps(
                                {
                                    "success": "Manager notified successfully.",
                                    "messageId": twilio_data["sid"],
                                    "isArrival": is_arrival,
                                }
                            )
                        )
                    else:
                        logger.warning("WhatsApp message sent, but no SID returned")
                        await result_callback(
                            json.dumps(
                                {
                                    "success": "Manager notified, but no message ID available.",
                                    "isArrival": is_arrival,
                                }
                            )
                        )
                else:
                    error_message = twilio_data.get("message", "Unknown error")
                    logger.error(f"Failed to send WhatsApp message: {error_message}")
                    await result_callback(
                        json.dumps({"error": f"Failed to send WhatsApp message: {error_message}"})
                    )
        except Exception as error:
            logger.error(f"Error in whatsappMessage function: {str(error)}")
            await result_callback(
                json.dumps({"error": "Failed to process the request.", "details": str(error)})
            )
