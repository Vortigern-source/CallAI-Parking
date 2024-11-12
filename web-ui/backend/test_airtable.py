import os
import json
import aiohttp
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_BOOKINGS_TABLE = os.getenv("AIRTABLE_BOOKINGS_TABLE")


async def test_airtable_connection():
    """Test Airtable API connection directly."""
    print(f"\nTesting Airtable connection...")
    print(f"Base ID: {AIRTABLE_BASE_ID}")
    print(f"Table: {AIRTABLE_BOOKINGS_TABLE}")

    headers = {"Authorization": f"Bearer {AIRTABLE_API_KEY}", "Content-Type": "application/json"}

    url = (
        f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_BOOKINGS_TABLE}?"
        "maxRecords=1&"  # Just get one record for testing
        "cellFormat=string&"
        "timeZone=Europe/London&"
        "userLocale=en-gb"
    )

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                print(f"\nResponse Status: {response.status}")
                print(f"Response Headers: {dict(response.headers)}")

                if response.status == 200:
                    data = await response.json()
                    print(f"\nSuccess! First record:")
                    print(json.dumps(data.get("records", [])[:1], indent=2))
                else:
                    text = await response.text()
                    print(f"\nError Response: {text}")

                return response.status == 200

    except Exception as e:
        print(f"\nError: {str(e)}")
        return False


if __name__ == "__main__":
    print("Starting Airtable connection test...")
    print(f"API Key: {'*' * len(AIRTABLE_API_KEY) if AIRTABLE_API_KEY else 'Not set'}")

    asyncio.run(test_airtable_connection())
