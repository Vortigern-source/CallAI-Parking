import asyncio
import os
import json
from dotenv import load_dotenv
from loguru import logger

# Load environment variables
load_dotenv()

# Import your functions here
from bot import update_terminal, update_registration, update_phone_number

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
        {"registration": "bb57chn", "terminal": "Terminal 2", "is_arrival": False},
        mock_llm,
        mock_context,
        result_callback,
    )


async def test_update_registration():
    print("\nTesting update_registration function:")
    await update_registration(
        "update_registration",
        "test_id",
        {"old_registration": "bb57chn", "new_registration": "XY34ZZZ", "is_arrival": False},
        mock_llm,
        mock_context,
        result_callback,
    )


async def test_update_phone_number():
    print("\nTesting update_phone_number function:")
    await update_phone_number(
        "update_phone_number",
        "test_id",
        {"registration": "bb57chn", "phone_number": "07123456789", "is_arrival": False},
        mock_llm,
        mock_context,
        result_callback,
    )


# Main function to run all tests
async def run_tests():
    await test_update_terminal()
    await test_update_registration()
    await test_update_phone_number()


# Run the tests
if __name__ == "__main__":
    asyncio.run(run_tests())
