import requests
from requests.auth import HTTPBasicAuth
import os

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")


async def hangup_call(
    call_sid,
    function_name,
    tool_call_id,
    args,
    llm,
    context,
    result_callback,
):
    url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Calls/{call_sid}.json"
    data = {"Status": "completed"}

    response = requests.post(
        url,
        data=data,
        auth=HTTPBasicAuth(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN),
    )

    # Check the response
    if response.status_code == 200:
        print(f"Call ended successfully: {call_sid}.")
    else:
        print(f"Error ending call: {response.status_code} - {response.text}")

    await result_callback()
