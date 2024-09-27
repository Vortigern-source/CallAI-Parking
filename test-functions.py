import asyncio
import os
import json
from dotenv import load_dotenv
from loguru import logger
from datetime import datetime
import pytz

# Load environment variables
load_dotenv()

# Import your functions here
from bot import (
    update_terminal,
    update_registration,
    update_phone_number,
    find_booking,
    transfer_call,
    whatsapp_message,
    find_booking_by_phone,
    update_eta,
    handle_get_current_time,
)

# Set up logger
logger.remove()
logger.add(lambda msg: print(msg, end=""))

# Mock LLM and context (we won't use these in our tests)
mock_llm = None
mock_context = None


# Callback function to handle results
async def result_callback(result):
    print(f"Result: {result}")


# Test functions
async def test_update_terminal():
    print("\nTesting update_terminal function:")
    await update_terminal(
        "update_terminal",
        "test_id",
        {"registration": "BB57CHN", "terminal": "Terminal 2", "is_arrival": False},
        mock_llm,
        mock_context,
        result_callback,
    )


async def test_update_registration():
    print("\nTesting update_registration function:")
    await update_registration(
        "update_registration",
        "test_id",
        {"old_registration": "BB57CHN", "new_registration": "XY34ZZZ", "is_arrival": False},
        mock_llm,
        mock_context,
        result_callback,
    )


async def test_update_phone_number():
    print("\nTesting update_phone_number function:")
    await update_phone_number(
        "update_phone_number",
        "test_id",
        {"registration": "BB57CHN", "phone_number": "07123456789", "is_arrival": False},
        mock_llm,
        mock_context,
        result_callback,
    )


async def test_find_booking():
    print("\nTesting find_booking function:")
    await find_booking(
        "find_booking",
        "test_id",
        {"registration": "BB57CHN", "is_arrival": False},
        mock_llm,
        mock_context,
        result_callback,
    )


async def test_transfer_call():
    print("\nTesting transfer_call function:")
    await transfer_call(
        "transfer_call",
        "test_id",
        {"call_sid": "CA123456789"},
        mock_llm,
        mock_context,
        result_callback,
    )


async def test_whatsapp_message():
    print("\nTesting whatsapp_message function:")
    await whatsapp_message(
        "whatsapp_message",
        "test_id",
        {"registration": "BB57CHN", "is_arrival": False},
        mock_llm,
        mock_context,
        result_callback,
    )


async def test_find_booking_by_phone():
    print("\nTesting find_booking_by_phone function:")
    await find_booking_by_phone(
        "find_booking_by_phone",
        "test_id",
        {"phone_number": "07123456789", "is_arrival": False},
        mock_llm,
        mock_context,
        result_callback,
    )


async def test_update_eta():
    print("\nTesting update_eta function:")
    await update_eta(
        "update_eta",
        "test_id",
        {"registration": "BB57CHN", "customer_eta": "30 minutes", "is_arrival": False},
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


# Main function to run all tests
async def run_tests():
    await test_update_terminal()
    await test_update_registration()
    await test_update_phone_number()
    await test_find_booking()
    await test_transfer_call()
    await test_whatsapp_message()
    await test_find_booking_by_phone()
    await test_update_eta()
    await test_get_current_time()


# Run the tests
if __name__ == "__main__":
    asyncio.run(run_tests())
