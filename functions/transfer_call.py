import os
import json
from twilio.rest import Client
from loguru import logger


async def transfer_call(function_name, tool_call_id, arguments, llm, context, result_callback):
    call_sid = arguments.get("call_sid")

    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    client = Client(account_sid, auth_token)

    logger.debug(f"Transferring call {call_sid}")

    try:
        client.calls(call_sid).update(
            twiml=f'<Response><Dial>{os.getenv("TRANSFER_NUMBER")}</Dial></Response>'
        )
        result = "The call was transferred successfully, say goodbye to the customer."
        await result_callback(json.dumps({"success": result}))
    except Exception as error:
        logger.error(f"Error transferring call: {str(error)}")
        await result_callback(json.dumps({"error": str(error)}))
