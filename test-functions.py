import asyncio
import os
import json
from dotenv import load_dotenv
from loguru import logger
from datetime import datetime
import pytz
import aiohttp

# Load environment variables
load_dotenv()

# Import your functions here
from functions import (
    find_booking,
    update_terminal,
    update_registration,
    update_phone_number,
    transfer_call,
    whatsapp_message,
    find_booking_by_phone,
    update_eta,
    handle_get_current_time,
    handle_get_current_date,
)
from functions.find_booking_by_ref import find_booking_by_ref  # Import the function directly
from functions.airtable_config import AIRTABLE_API_KEY, AIRTABLE_BASE_ID, AIRTABLE_BOOKINGS_TABLE

# Set up logger
logger.remove()
logger.add(lambda msg: print(msg, end=""))

# Mock LLM and context (we won't use these in our tests)
mock_llm = None
mock_context = None


# Callback function to handle results
async def result_callback(result):
    print(f"Result: {result}")
    return result


async def reset_driver_status():
    """Reset the driver status in Airtable"""
    url = (
        f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_BOOKINGS_TABLE}?"
        f'filterByFormula=UPPER({{Registration}})=UPPER("BF11KKG")&'
        f"cellFormat=string&timeZone=Europe/London&userLocale=en-gb"
    )

    headers = {"Authorization": f"Bearer {AIRTABLE_API_KEY}"}

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                if data["records"]:
                    record = data["records"][0]
                    record_id = record["id"]

                    patch_url = (
                        f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_BOOKINGS_TABLE}"
                    )
                    patch_data = {
                        "records": [
                            {
                                "id": record_id,
                                "fields": {
                                    "Drop_Off_Status": "Pending",
                                    "Collection_Status": "Pending",
                                },
                            }
                        ],
                        "typecast": True,
                    }

                    async with session.patch(
                        patch_url, headers=headers, json=patch_data
                    ) as patch_response:
                        if patch_response.status == 200:
                            print("Reset driver status to Pending")
                        else:
                            print(f"Failed to reset status: {await patch_response.text()}")


# Test functions
async def test_update_terminal():
    print("\nTesting update_terminal function:")
    await update_terminal(
        "update_terminal",
        "test_id",
        {"registration": "BF11KKG", "terminal": "Terminal 2"},
        mock_llm,
        mock_context,
        result_callback,
    )


async def test_update_registration():
    print("\nTesting update_registration function:")
    await update_registration(
        "update_registration",
        "test_id",
        {"old_registration": "BF11KKG", "new_registration": "XY34ZZZ"},
        mock_llm,
        mock_context,
        result_callback,
    )


async def test_update_phone_number():
    print("\nTesting update_phone_number function:")
    result = await update_phone_number(
        "update_phone_number",
        "test_id",
        {"registration": "BF11KKG", "phone_number": "07421117301"},
        mock_llm,
        mock_context,
        result_callback,
    )
    return result


async def test_find_booking():
    print("\nTesting find_booking function:")
    await find_booking(
        "find_booking",
        "test_id",
        {"registration": "BF11KKG"},
        mock_llm,
        mock_context,
        result_callback,
    )


async def test_whatsapp_message(context=None):
    print("\nTesting whatsapp_message function:")
    await whatsapp_message(
        "whatsapp_message",
        "test_id",
        {"registration": "BF11KKG", "is_drop_off": True},
        mock_llm,
        context,
        result_callback,
    )


async def test_find_booking_by_phone():
    print("\nTesting find_booking_by_phone function:")
    await find_booking_by_phone(
        "find_booking_by_phone",
        "test_id",
        {"phone_number": "07421117301"},
        mock_llm,
        mock_context,
        result_callback,
    )


async def test_update_eta():
    print("\nTesting update_eta function with various formats:")

    # Test relative time formats
    print("\nTesting with relative time (20 minutes):")
    await update_eta(
        "update_eta",
        "test_id",
        {"registration": "BF11KKG", "customer_eta": "20 minutes"},
        mock_llm,
        mock_context,
        result_callback,
    )

    print("\nTesting with relative time (2 hours):")
    await update_eta(
        "update_eta",
        "test_id",
        {"registration": "BF11KKG", "customer_eta": "2 hours"},
        mock_llm,
        mock_context,
        result_callback,
    )

    # Test absolute time formats
    # Get current hour in 24-hour format to ensure we test with a future time
    current_hour = datetime.now().hour
    test_hour = (current_hour + 2) % 24  # 2 hours in the future
    test_hour_12 = test_hour if test_hour <= 12 else test_hour - 12
    ampm = "AM" if test_hour < 12 else "PM"

    print(f"\nTesting with 12-hour format ({test_hour_12}:30 {ampm}):")
    await update_eta(
        "update_eta",
        "test_id",
        {"registration": "BF11KKG", "customer_eta": f"{test_hour_12}:30 {ampm}"},
        mock_llm,
        mock_context,
        result_callback,
    )

    print(f"\nTesting with 24-hour format ({test_hour:02d}:30):")
    await update_eta(
        "update_eta",
        "test_id",
        {"registration": "BF11KKG", "customer_eta": f"{test_hour:02d}:30"},
        mock_llm,
        mock_context,
        result_callback,
    )

    # Test special case for collections
    print("\nTesting with 'Customer has collected luggage':")
    await update_eta(
        "update_eta",
        "test_id",
        {"registration": "BF11KKG", "customer_eta": "Customer has collected luggage"},
        mock_llm,
        mock_context,
        result_callback,
    )


async def test_get_current_time():
    print("\nTesting get_current_time function:")
    await handle_get_current_time(
        "get_current_time",
        "test_id",
        {},
        mock_llm,
        mock_context,
        result_callback,
    )


async def test_get_current_date():
    print("\nTesting get_current_date function:")
    await handle_get_current_date(
        "get_current_date",
        "test_id",
        {},
        mock_llm,
        mock_context,
        result_callback,
    )


async def test_find_booking_by_ref():
    print("\nTesting find_booking_by_ref function with various formats:")

    # Test without dashes
    print("\nTesting without dashes (GLMAN78961):")
    await find_booking_by_ref(
        "find_booking_by_ref",
        "test_id",
        {"booking_ref": "GLMAN78961"},
        mock_llm,
        mock_context,
        result_callback,
    )

    # Test CPD format without dashes
    print("\nTesting CPD format without dashes (CPD19581405):")
    await find_booking_by_ref(
        "find_booking_by_ref",
        "test_id",
        {"booking_ref": "CPD19581405"},
        mock_llm,
        mock_context,
        result_callback,
    )


# Main function to run all tests
async def run_tests():
    print("\nStep 1: Resetting driver status")
    await reset_driver_status()

    print("\nStep 2: Updating phone number")
    result = await test_update_phone_number()

    # Extract context from the result
    context = None
    if isinstance(result, str):
        try:
            parsed_result = json.loads(result)
            print(f"\nParsed result: {parsed_result}")

            # Phone numbers are in the root level
            old_phone = parsed_result.get("oldPhoneNumber")
            new_phone = parsed_result.get("updatedPhoneNumber")

            if old_phone and new_phone:
                context = {"oldPhoneNumber": old_phone, "updatedPhoneNumber": new_phone}
                print(f"\nContext for WhatsApp message: {context}")
                print(f"Old phone: {old_phone}")
                print(f"New phone: {new_phone}")
        except Exception as e:
            print(f"Error parsing result: {e}")
            print(f"Raw result: {result}")

    print("\nStep 3: Testing WhatsApp message to see the change")
    await test_whatsapp_message(context)


# Run the tests
if __name__ == "__main__":
    asyncio.run(run_tests())
