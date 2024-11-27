# Standard
import json
import os
from dotenv import load_dotenv
import uvicorn
import requests
from requests.auth import HTTPBasicAuth
from fastapi import FastAPI, WebSocket, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import HTMLResponse
from loguru import logger

# Twilio
from twilio.twiml.voice_response import VoiceResponse

# Internal
from bot import run_bot
from custom_pipecat.twilio_utils.twilio_recordings import start_recording
from twilio.rest import Client as TwilioClient

# Load .env file with explicit path
load_dotenv(dotenv_path=".env")

# Verify Twilio credentials
account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
auth_token = os.environ.get("TWILIO_AUTH_TOKEN")

if not account_sid or not auth_token:
    logger.error("Twilio credentials not found in environment variables!")
    logger.error(f"Account SID: {account_sid}")
    logger.error(f"Auth Token: {'*' * len(auth_token) if auth_token else 'Not Set'}")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/start_call")
def announce_recording():
    # Create a TwiML response
    resp = VoiceResponse()
    logger.info(f"Resp: {resp}")
    # Have the bot say something
    resp.say(
        "This call may be recorded for quality assurance purposes.",
        voice="Polly.En-US-Neural-A",
        language="en-US",
    )
    # Redirect to another URL to start the call and the recording
    resp.redirect("/start_call")
    # return Response(content=str(resp), media_type="application/xml")
    return HTMLResponse(
        content=open("custom_pipecat/templates/streams.xml").read(), media_type="application/xml"
    )


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # Accept websocket connection and get call data
    await websocket.accept()
    start_data = websocket.iter_text()
    await start_data.__anext__()
    call_data = json.loads(await start_data.__anext__())
    logger.info(f"Start data: {start_data}")
    logger.info(call_data)
    logger.info("WebSocket connection accepted")

    # Extract the Call SID and Stream SID from the Twilio start event data
    stream_sid, call_sid = call_data["start"]["streamSid"], call_data["start"]["callSid"]

    # Start recording
    account_sid, auth_token = (
        os.environ.get("TWILIO_ACCOUNT_SID"),
        os.environ.get("TWILIO_AUTH_TOKEN"),
    )
    logger.info(f"Account SID: {account_sid}")

    # Add additional error checking before creating TwilioClient
    if not account_sid or not auth_token:
        logger.error("Cannot create Twilio client: Missing credentials")
        raise ValueError("Twilio credentials are required")

    twilio_client = TwilioClient(
        account_sid, auth_token, None, None
    )  # Hardcoded, will not work if calling a Twilio phone number routed through another route
    await start_recording(call_sid, twilio_client)
    call_info = twilio_client.calls(call_sid).fetch()
    await run_bot(websocket, stream_sid, call_sid, call_info)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8765)
