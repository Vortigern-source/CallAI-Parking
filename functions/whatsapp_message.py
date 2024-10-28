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
    is_drop_off = arguments.get("isDropOff")

    if is_drop_off is None:
        await result_callback(json.dumps({"error": "isDropOff parameter is required"}))
        return

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

    headers = {"Authorization": f"Bearer {AIRTABLE_API_KEY}"}

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(airtable_url, headers=headers) as response:
                airtable_data = await response.json()

            if airtable_data["records"]:
                record = airtable_data["records"][0]["fields"]

                # Check if a driver has already been requested
                status_field = "Drop_Off_Status" if is_drop_off else "Collection_Status"
                if record.get(status_field) == "Driver Requested":
                    logger.info(
                        f"Driver already requested for booking: {record.get('Booking_Ref', 'N/A')}"
                    )
                    await result_callback(
                        json.dumps(
                            {
                                "success": "Driver already requested.",
                                "isDropOff": is_drop_off,
                            }
                        )
                    )
                    return

                booking_ref = record.get("Booking_Ref", "N/A")
                vehicle_make = record.get("Vehicle_Make", "N/A")
                name = record.get("Name", "N/A")
                contact_number = record.get("Contact_Number", "N/A")
                entry_date_time = record.get("Entry_Date_Time", "N/A")
                terminal = record.get("Terminal", "N/A")
                estimated_eta = record.get("Current_ETA", "N/A")
                allocated_car_park = record.get("Allocated_Car_Park", "N/A")
                old_terminal = record.get("Old_Terminal", "N/A")
                old_registration = record.get("Old_Registration", "N/A")
                old_phone_number = record.get("Old_Phone_Number", "N/A")

                booking_type = "Car Drop-off" if is_drop_off else "Car Collection"

                message = f"""
New Booking - {booking_type}:
- Booking Reference: {booking_ref}
- Vehicle: {vehicle_make} ({registration})
- Customer Name: {name}
- Contact Number: {contact_number}
- {"Drop-off" if is_drop_off else "Collection"} Date/Time: {entry_date_time}
- Estimated {"Drop-off" if is_drop_off else "Arrival"} Time: {"" if is_drop_off else "Customer has collected luggage"}
- Terminal: {terminal}
- Allocated Car Park: {allocated_car_park}
"""

                # Add changes section only if there are changes
                changes = []
                if old_terminal and old_terminal != terminal:
                    changes.append(f"- Terminal changed from {old_terminal} to {terminal}")
                if old_registration and old_registration != registration:
                    changes.append(
                        f"- Registration changed from {old_registration} to {registration}"
                    )
                if old_phone_number and old_phone_number != contact_number:
                    changes.append(
                        f"- Phone number changed from {old_phone_number} to {contact_number}"
                    )
                if changes:
                    message += "\nRecent Changes:\n" + "\n".join(changes)

                message += f'\nAction Required: Please assign a driver for this {{"drop-off" if is_drop_off else "collection"}}.'

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
                                    "isDropOff": is_drop_off,
                                }
                            )
                        )
                    else:
                        logger.warning("WhatsApp message sent, but no SID returned")
                        await result_callback(
                            json.dumps(
                                {
                                    "success": "Manager notified, but no message ID available.",
                                    "isDropOff": is_drop_off,
                                }
                            )
                        )
                else:
                    error_message = twilio_data.get("message", "Unknown error")
                    logger.error(f"Failed to send WhatsApp message: {error_message}")
                    await result_callback(
                        json.dumps({"error": f"Failed to send WhatsApp message: {error_message}"})
                    )

                # Update the status in Airtable
                status_field = "Drop_Off_Status" if is_drop_off else "Collection_Status"
                status_value = "Driver Requested"
                eta_value = "" if is_drop_off else "Customer has collected luggage"

                patch_url = (
                    f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_BOOKINGS_TABLE}"
                )
                patch_data = {
                    "records": [
                        {
                            "id": airtable_data["records"][0]["id"],
                            "fields": {status_field: status_value, "Current_ETA": eta_value},
                        }
                    ],
                    "typecast": True,
                }

                async with session.patch(
                    patch_url, headers=headers, json=patch_data
                ) as patch_response:
                    if patch_response.status == 200:
                        logger.info(
                            f"Updated {status_field} to {status_value} and Current_ETA to {eta_value}"
                        )
                    else:
                        logger.error(f"Failed to update {status_field} and Current_ETA")

            else:
                logger.warning(f"No booking found for registration: {formatted_registration}")
                await result_callback(
                    json.dumps({"error": "No booking found for this registration number."})
                )
        except Exception as error:
            logger.error(f"Error in whatsappMessage function: {str(error)}")
            await result_callback(
                json.dumps({"error": "Failed to process the request.", "details": str(error)})
            )


# Add this new function to the existing whatsapp_message.py file


async def whatsapp_message_extension(
    function_name, tool_call_id, booking_details, llm, context, result_callback
):
    twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    twilio_whatsapp_number = os.getenv("TWILIO_WHATSAPP_NUMBER")
    manager_whatsapp_group = os.getenv("MANAGER_WHATSAPP_GROUP")

    message = f"""
Booking Extension Required:
- Booking Reference: {booking_details.get('bookingRef', 'N/A')}
- Vehicle: {booking_details.get('vehicleMake', 'N/A')} ({booking_details.get('registration', 'N/A')})
- Customer Name: {booking_details.get('customerName', 'N/A')}
- Contact Number: {booking_details.get('contactNumber', 'N/A')}
- Original End Date/Time: {booking_details.get('endDate', 'N/A')}
- Terminal: {booking_details.get('terminal', 'N/A')}
- Allocated Car Park: {booking_details.get('allocatedCarPark', 'N/A')}

This customer's booking has expired, and they wish to extend it. Please contact the customer to arrange the extension and additional payment.
"""

    logger.debug(f"WhatsApp message content for extension: {message}")

    twilio_url = f"https://api.twilio.com/2010-04-01/Accounts/{twilio_account_sid}/Messages.json"
    auth = aiohttp.BasicAuth(twilio_account_sid, twilio_auth_token)
    data = {
        "From": f"whatsapp:{twilio_whatsapp_number}",
        "To": f"whatsapp:{manager_whatsapp_group}",
        "Body": message,
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                twilio_url,
                auth=auth,
                data=urlencode(data),
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            ) as twilio_response:
                twilio_data = await twilio_response.json()

            if twilio_response.status == 201:
                if "sid" in twilio_data:
                    logger.info(
                        f'WhatsApp message for extension sent successfully: {twilio_data["sid"]}'
                    )
                    await result_callback(
                        json.dumps(
                            {
                                "success": "Manager notified about booking extension.",
                                "messageId": twilio_data["sid"],
                            }
                        )
                    )
                else:
                    logger.warning("WhatsApp message for extension sent, but no SID returned")
                    await result_callback(
                        json.dumps(
                            {
                                "success": "Manager notified about booking extension, but no message ID available.",
                            }
                        )
                    )
            else:
                error_message = twilio_data.get("message", "Unknown error")
                logger.error(f"Failed to send WhatsApp message for extension: {error_message}")
                await result_callback(
                    json.dumps(
                        {"error": f"Failed to send WhatsApp message for extension: {error_message}"}
                    )
                )
        except Exception as error:
            logger.error(f"Error in whatsappMessageExtension function: {str(error)}")
            await result_callback(
                json.dumps(
                    {"error": "Failed to process the extension request.", "details": str(error)}
                )
            )
