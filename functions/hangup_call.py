import requests
from requests.auth import HTTPBasicAuth
import os

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")

from twilio.rest import Client


async def get_twilio_client(account_sid: str, auth_token: str, region: str, edge: str):
    return Client(account_sid, auth_token, region=region, edge=edge)


async def hangup_call(
    call_sid: str,
    twillio_client: Client,
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
