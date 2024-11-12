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
    # Remove all non-digit characters
    cleaned = "".join(filter(str.isdigit, str(phone)))
    # Handle international format
    if cleaned.startswith("44"):
        cleaned = "0" + cleaned[2:]
    elif not cleaned.startswith("0"):
        cleaned = "0" + cleaned
    # Ensure 11 digits for UK numbers
    if len(cleaned) == 10:  # Missing leading 0
        cleaned = "0" + cleaned
    return cleaned


async def whatsapp_message(function_name, tool_call_id, arguments, llm, context, result_callback):
    """
    Send a WhatsApp message to notify staff about a booking that needs a driver.
    Compares initial booking details with fresh Airtable data to show changes.
    """
    try:
        # Log the received context
        logger.debug(f"Received context in whatsapp_message: {context}")

        # Get initial details from the LLM context messages
        initial_details = None
        if llm and hasattr(llm, "context") and hasattr(llm.context, "messages"):
            for message in reversed(llm.context.messages):
                if message.get("role") == "function" and message.get("name") == "find_booking":
                    try:
                        result = json.loads(message.get("content", "{}"))
                        if result.get("success"):
                            initial_details = result.get("result", {})
                            logger.debug(f"Found initial details: {initial_details}")
                            break
                    except json.JSONDecodeError:
                        logger.warning("Failed to parse find_booking result")

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

                # For drop-offs, check if ETA exists
                if is_drop_off:
                    estimated_eta = record.get("Current_ETA")
                    if not estimated_eta or estimated_eta == "N/A":
                        error_msg = "ETA is required for drop-offs. Please update the ETA before requesting a driver."
                        logger.warning(error_msg)
                        await result_callback(create_response(False, error_msg))
                        return

                # Extract booking details from fresh lookup
                booking_ref = record.get("Booking_Ref", "N/A")
                vehicle_make = record.get("Vehicle_Make", "N/A")
                name = record.get("Name", "N/A")
                contact_number = record.get("Contact_Number", "N/A")
                entry_date_time = record.get("Entry_Date_Time", "N/A")
                terminal = record.get("Terminal", "N/A")
                allocated_car_park = record.get("Allocated_Car_Park", "N/A")

                # Format fields for display
                registration_text = registration.replace("-", "")  # Remove dashes from registration
                contact_text = contact_number  # Use raw phone number without formatting
                display_entry_time = format_date_for_display(entry_date_time)

                # Handle ETA display based on booking type
                if is_drop_off:
                    estimated_eta = record.get("Current_ETA", "N/A")
                    display_eta = (
                        format_date_for_display(estimated_eta)
                        if estimated_eta != "N/A"
                        else estimated_eta
                    )
                else:
                    # For collections, always show "Customer has collected luggage"
                    display_eta = "Customer has collected luggage"

                # Compare with initial details if available
                changes = []
                if initial_details:
                    # Compare phone numbers
                    initial_phone = initial_details.get("contactNumber")
                    if initial_phone and initial_phone != contact_number:
                        changes.append(
                            f"Phone number changed from {initial_phone} to {contact_number}"
                        )

                    # Compare vehicle details
                    initial_vehicle = initial_details.get("vehicleMake")
                    if initial_vehicle and initial_vehicle != vehicle_make:
                        changes.append(
                            f"Vehicle details changed from {initial_vehicle} to {vehicle_make}"
                        )

                    # Compare terminal
                    initial_terminal = initial_details.get("terminal")
                    if initial_terminal and initial_terminal != terminal:
                        changes.append(f"Terminal changed from {initial_terminal} to {terminal}")
                        changes.append(
                            f"Car park changed from {initial_details.get('allocatedCarPark', 'N/A')} to {allocated_car_park}"
                        )

                # Check for updates in context (these override both initial and fresh details)
                if context and isinstance(context, dict):
                    # Handle phone number update
                    old_phone = context.get("oldPhoneNumber")
                    new_phone = context.get("updatedPhoneNumber")
                    if old_phone and new_phone and old_phone != new_phone:
                        contact_text = new_phone
                        changes = [c for c in changes if not c.startswith("Phone number changed")]
                        changes.append(f"Phone number changed from {old_phone} to {new_phone}")

                    # Handle terminal update
                    old_terminal = context.get("oldTerminal")
                    new_terminal = context.get("updatedTerminal")
                    if old_terminal and new_terminal and old_terminal != new_terminal:
                        terminal = new_terminal
                        changes = [c for c in changes if not c.startswith("Terminal changed")]
                        changes.append(f"Terminal changed from {old_terminal} to {new_terminal}")
                        # Add car park change when terminal changes
                        old_car_park = (
                            initial_details.get("allocatedCarPark") if initial_details else "N/A"
                        )
                        changes = [c for c in changes if not c.startswith("Car park changed")]
                        changes.append(
                            f"Car park changed from {old_car_park} to {allocated_car_park}"
                        )

                    # Handle vehicle details update
                    old_vehicle_make = context.get("oldVehicleMake")
                    new_vehicle_make = context.get("updatedVehicleMake")
                    if (
                        old_vehicle_make
                        and new_vehicle_make
                        and old_vehicle_make != new_vehicle_make
                    ):
                        vehicle_make = new_vehicle_make
                        changes = [
                            c for c in changes if not c.startswith("Vehicle details changed")
                        ]
                        changes.append(
                            f"Vehicle details changed from {old_vehicle_make} to {new_vehicle_make}"
                        )

                booking_type = "Car Drop-off" if is_drop_off else "Car Collection"
                message = f"""
New Booking - {booking_type}:
- Booking Reference: {booking_ref}
- Vehicle: {vehicle_make} ({registration_text})
- Customer Name: {name}
- Contact Number: {contact_text}
- {"Drop-off" if is_drop_off else "Collection"} Date & Time: {display_entry_time}
- Estimated {"Drop-off" if is_drop_off else "Arrival"} Time: {display_eta}
- Terminal: {terminal}
- Allocated Car Park: {allocated_car_park}
"""

                # Add changes section if there are any changes
                if changes:
                    message += "\nChanges Detected:\n"
                    for change in changes:
                        message += f"- {change}\n"

                message += f"\nAction Required: Please assign a driver for this {'drop-off' if is_drop_off else 'collection'}."

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
- Original End Date & Time: {end_date}
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
