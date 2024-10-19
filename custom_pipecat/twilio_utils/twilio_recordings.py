from twilio.rest import Client


async def get_twilio_client(account_sid: str, auth_token: str, region: str, edge: str):
    return Client(account_sid, auth_token, region=region, edge=edge)


from twilio.rest import Client
from loguru import logger


async def start_recording(call_sid: str, twilio_client: Client):
    try:
        # Start recording the call
        call = twilio_client.calls(call_sid).recordings.create()
        logger.info(f"Recording started for call SID: {call.sid}")
    except Exception as e:
        logger.error(f"An error occurred while starting the recording: {e}")
    return
