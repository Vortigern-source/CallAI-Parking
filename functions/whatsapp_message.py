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
from .utils import (
    create_response,
    format_registration,
    format_date_for_display,
    format_phone_for_display,
    format_registration_for_display,
)


def clean_phone_number(phone):
    """Remove any formatting from phone number"""
    if not phone:
        return None
    return "".join(filter(str.isdigit, str(phone)))


async def whatsapp_message(function_name, tool_call_id, arguments, llm, context, result_callback):
    """
    Send a WhatsApp message to notify staff about a booking that needs a driver.
    Fetches fresh booking data from Airtable and includes any changed details inline.
    """
    try:
        # Log the received context
        logger.debug(f"Received context in whatsapp_message: {context}")

        # Validate required arguments
        if not arguments.get("registration") or "is_drop_off" not in arguments:
            await result_callback(
                create_response(False, "Registration and is_drop_off are required")
            )
            return

        registration = arguments["registration"]
        is_drop_off = arguments["is_drop_off"]
        status_field = "Drop_Off_Status" if is_drop_off else "Collection_Status"

        # Validate environment variables
        required_env_vars = [
            ("TWILIO_ACCOUNT_SID", os.getenv("TWILIO_ACCOUNT_SID")),
            ("TWILIO_AUTH_TOKEN", os.getenv("TWILIO_AUTH_TOKEN")),
            ("TWILIO_WHATSAPP_NUMBER", os.getenv("TWILIO_WHATSAPP_NUMBER")),
            ("MANAGER_WHATSAPP_GROUP", os.getenv("MANAGER_WHATSAPP_GROUP")),
            ("AIRTABLE_API_KEY", AIRTABLE_API_KEY),
            ("AIRTABLE_BASE_ID", AIRTABLE_BASE_ID),
            ("AIRTABLE_BOOKINGS_TABLE", AIRTABLE_BOOKINGS_TABLE),
        ]

        missing_env_vars = [name for name, value in required_env_vars if not value]
        if missing_env_vars:
            error_msg = f"Missing required environment variables: {', '.join(missing_env_vars)}"
            logger.error(error_msg)
            await result_callback(create_response(False, error_msg))
            return

        formatted_registration = format_registration(registration)

        # Get fresh data from Airtable
        airtable_url = (
            f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_BOOKINGS_TABLE}?"
            f'filterByFormula=UPPER({{Registration}})=UPPER("{formatted_registration}")&'
            f"cellFormat=string&timeZone=Europe/London&userLocale=en-gb"
        )

        headers = {"Authorization": f"Bearer {AIRTABLE_API_KEY}"}

        async with aiohttp.ClientSession() as session:
            async with session.get(airtable_url, headers=headers) as response:
                if response.status != 200:
                    error_msg = f"Failed to fetch booking data: {await response.text()}"
                    logger.error(error_msg)
                    await result_callback(create_response(False, error_msg))
                    return

                airtable_data = await response.json()

                if not airtable_data.get("records"):
                    error_msg = f"No booking found for registration: {formatted_registration}"
                    logger.warning(error_msg)
                    await result_callback(create_response(False, error_msg))
                    return

                record = airtable_data["records"][0]["fields"]

                # Check if a driver has already been requested
                if record.get(status_field) == "Driver Requested":
                    msg = (
                        f"Driver already requested for booking: {record.get('Booking_Ref', 'N/A')}"
                    )
                    logger.info(msg)
                    await result_callback(create_response(True, msg, {"is_drop_off": is_drop_off}))
                    return

                # Extract booking details
                booking_ref = record.get("Booking_Ref", "N/A")
                vehicle_make = record.get("Vehicle_Make", "N/A")
                name = record.get("Name", "N/A")
                contact_number = record.get("Contact_Number", "N/A")
                entry_date_time = record.get("Entry_Date_Time", "N/A")
                terminal = record.get("Terminal", "N/A")
                estimated_eta = record.get("Current_ETA", "N/A")
                allocated_car_park = record.get("Allocated_Car_Park", "N/A")

                # Format fields for display
                registration_text = registration.replace("-", "")  # Remove dashes from registration
                contact_text = contact_number  # Use raw phone number without formatting
                display_entry_time = format_date_for_display(entry_date_time)
                display_eta = estimated_eta
                if estimated_eta != "Customer has collected luggage":
                    display_eta = format_date_for_display(estimated_eta)

                # Check for old phone number in context
                if context and isinstance(context, dict):
                    old_phone = context.get("oldPhoneNumber")
                    new_phone = context.get("updatedPhoneNumber")
                    logger.debug(f"Phone number comparison - Old: {old_phone}, New: {new_phone}")

                    # Clean phone numbers for comparison
                    clean_old = clean_phone_number(old_phone)
                    clean_new = clean_phone_number(new_phone)

                    if clean_old and clean_new and clean_old != clean_new:
                        contact_text = f"{new_phone} (Changed from {old_phone} to {new_phone})"
                        logger.debug(f"Updated contact_text with change message: {contact_text}")
                    else:
                        logger.debug(
                            f"Phone numbers are the same after cleaning: {clean_old} = {clean_new}"
                        )

                # Check for old terminal in context
                if context and isinstance(context, dict):
                    old_terminal = context.get("oldTerminal")
                    new_terminal = context.get("updatedTerminal")
                    logger.debug(f"Terminal comparison - Old: {old_terminal}, New: {new_terminal}")

                    if old_terminal and new_terminal and old_terminal != new_terminal:
                        terminal = f"{new_terminal} (Changed from {old_terminal} to {new_terminal})"
                        logger.debug(f"Updated terminal with change message: {terminal}")

                # Check for old vehicle details in context
                if context and isinstance(context, dict):
                    old_vehicle_make = context.get("oldVehicleMake")
                    new_vehicle_make = context.get("updatedVehicleMake")
                    logger.debug(
                        f"Vehicle details comparison - Old: {old_vehicle_make}, New: {new_vehicle_make}"
                    )

                    if (
                        old_vehicle_make
                        and new_vehicle_make
                        and old_vehicle_make != new_vehicle_make
                    ):
                        vehicle_make = f"{new_vehicle_make} (Changed from {old_vehicle_make} to {new_vehicle_make})"
                        logger.debug(f"Updated vehicle details with change message: {vehicle_make}")

                booking_type = "Car Drop-off" if is_drop_off else "Car Collection"
                message = f"""
New Booking - {booking_type}:
- Booking Reference: {booking_ref}
- Vehicle: {vehicle_make} ({registration_text})
- Customer Name: {name}
- Contact Number: {contact_text}
- {"Drop-off" if is_drop_off else "Collection"} Date/Time: {display_entry_time}
- Estimated {"Drop-off" if is_drop_off else "Arrival"} Time: {display_eta}
- Terminal: {terminal}
- Allocated Car Park: {allocated_car_park}

Action Required: Please assign a driver for this {"drop-off" if is_drop_off else "collection"}.
"""

                logger.debug(f"WhatsApp message content: {message}")

                # Send WhatsApp message
                twilio_url = f"https://api.twilio.com/2010-04-01/Accounts/{os.getenv('TWILIO_ACCOUNT_SID')}/Messages.json"
                auth = aiohttp.BasicAuth(
                    os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN")
                )
                data = {
                    "From": f"whatsapp:{os.getenv('TWILIO_WHATSAPP_NUMBER')}",
                    "To": f"whatsapp:{os.getenv('MANAGER_WHATSAPP_GROUP')}",
                    "Body": message,
                }

                async with session.post(
                    twilio_url,
                    auth=auth,
                    data=urlencode(data),
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                ) as twilio_response:
                    twilio_data = await twilio_response.json()

                    if twilio_response.status != 201:
                        error_msg = f"Failed to send WhatsApp message: {twilio_data.get('message', 'Unknown error')}"
                        logger.error(error_msg)
                        await result_callback(create_response(False, error_msg))
                        return

                    # Update Airtable status
                    patch_url = (
                        f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_BOOKINGS_TABLE}"
                    )
                    patch_data = {
                        "records": [
                            {
                                "id": airtable_data["records"][0]["id"],
                                "fields": {status_field: "Driver Requested"},
                            }
                        ],
                        "typecast": True,
                    }

                    async with session.patch(
                        patch_url, headers=headers, json=patch_data
                    ) as patch_response:
                        if patch_response.status != 200:
                            logger.error(f"Failed to update {status_field}")
                            # Don't return error since message was sent successfully
                        else:
                            logger.info(f"Updated {status_field} to Driver Requested")

                    # Return success response
                    success_msg = "Manager notified successfully."
                    if "sid" in twilio_data:
                        logger.info(f'WhatsApp message sent successfully: {twilio_data["sid"]}')
                        await result_callback(
                            create_response(
                                True,
                                success_msg,
                                {
                                    "messageId": twilio_data["sid"],
                                    "is_drop_off": is_drop_off,
                                },
                            )
                        )
                    else:
                        logger.warning("WhatsApp message sent, but no SID returned")
                        await result_callback(
                            create_response(
                                True,
                                success_msg,
                                {
                                    "is_drop_off": is_drop_off,
                                },
                            )
                        )

    except Exception as error:
        error_msg = f"Error in whatsappMessage function: {str(error)}"
        logger.error(error_msg)
        await result_callback(create_response(False, error_msg))


async def whatsapp_message_extension(
    function_name, tool_call_id, booking_details, llm, context, result_callback
):
    """Send a WhatsApp message to notify staff about a booking that needs extension."""
    try:
        # Validate environment variables
        required_env_vars = [
            ("TWILIO_ACCOUNT_SID", os.getenv("TWILIO_ACCOUNT_SID")),
            ("TWILIO_AUTH_TOKEN", os.getenv("TWILIO_AUTH_TOKEN")),
            ("TWILIO_WHATSAPP_NUMBER", os.getenv("TWILIO_WHATSAPP_NUMBER")),
            ("MANAGER_WHATSAPP_GROUP", os.getenv("MANAGER_WHATSAPP_GROUP")),
        ]

        missing_env_vars = [name for name, value in required_env_vars if not value]
        if missing_env_vars:
            error_msg = f"Missing required environment variables: {', '.join(missing_env_vars)}"
            logger.error(error_msg)
            await result_callback(create_response(False, error_msg))
            return

        # Format fields for display
        registration = booking_details.get("registration", "N/A")
        contact_number = booking_details.get("contactNumber", "N/A")
        end_date = booking_details.get("endDate", "N/A")

        registration_display = registration.replace("-", "")  # Remove dashes from registration
        contact_display = contact_number  # Use raw phone number without formatting

        message = f"""
Booking Extension Required:
- Booking Reference: {booking_details.get('bookingRef', 'N/A')}
- Vehicle: {booking_details.get('vehicleMake', 'N/A')} ({registration_display})
- Customer Name: {booking_details.get('customerName', 'N/A')}
- Contact Number: {contact_display}
- Original End Date/Time: {end_date}
- Terminal: {booking_details.get('terminal', 'N/A')}
- Allocated Car Park: {booking_details.get('allocatedCarPark', 'N/A')}

This customer's booking has expired, and they wish to extend it. Please contact the customer to arrange the extension and additional payment.
"""

        logger.debug(f"WhatsApp message content for extension: {message}")

        twilio_url = f"https://api.twilio.com/2010-04-01/Accounts/{os.getenv('TWILIO_ACCOUNT_SID')}/Messages.json"
        auth = aiohttp.BasicAuth(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
        data = {
            "From": f"whatsapp:{os.getenv('TWILIO_WHATSAPP_NUMBER')}",
            "To": f"whatsapp:{os.getenv('MANAGER_WHATSAPP_GROUP')}",
            "Body": message,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                twilio_url,
                auth=auth,
                data=urlencode(data),
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            ) as twilio_response:
                twilio_data = await twilio_response.json()

                if twilio_response.status != 201:
                    error_msg = f"Failed to send WhatsApp message for extension: {twilio_data.get('message', 'Unknown error')}"
                    logger.error(error_msg)
                    await result_callback(create_response(False, error_msg))
                    return

                # Return success response
                success_msg = "Manager notified about booking extension."
                if "sid" in twilio_data:
                    logger.info(
                        f'WhatsApp message for extension sent successfully: {twilio_data["sid"]}'
                    )
                    await result_callback(
                        create_response(
                            True,
                            success_msg,
                            {
                                "messageId": twilio_data["sid"],
                            },
                        )
                    )
                else:
                    logger.warning("WhatsApp message for extension sent, but no SID returned")
                    await result_callback(create_response(True, success_msg))

    except Exception as error:
        error_msg = f"Error in whatsappMessageExtension function: {str(error)}"
        logger.error(error_msg)
        await result_callback(create_response(False, error_msg))
