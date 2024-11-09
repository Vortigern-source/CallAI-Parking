import os
import sys
import re
import aiohttp
import asyncio
from loguru import logger
import logging

from typing import List, Dict
from dotenv import load_dotenv
import json
from datetime import datetime
from openai.types.chat import ChatCompletionToolParam

# Pipecat imports
from pipecat.frames.frames import (
    EndFrame,
    LLMMessagesFrame,
    Frame,
    TranscriptionFrame,
    TextFrame,
    LLMFullResponseStartFrame,
    LLMFullResponseEndFrame,
    TTSStartedFrame,
    TTSStoppedFrame,
    BotStartedSpeakingFrame,
    BotStoppedSpeakingFrame,
    BotSpeakingFrame,
    TTSAudioRawFrame,
    OutputAudioRawFrame,
)

from pipecat.services.openai import OpenAILLMContext
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask, FrameProcessor, FrameDirection
from pipecat.processors.aggregators.llm_response import (
    LLMAssistantResponseAggregator,
    LLMUserResponseAggregator,
)

from pipecat.services.openai import OpenAILLMService
from pipecat.utils.text.markdown_text_filter import MarkdownTextFilter
from pipecat.services.cartesia import CartesiaTTSService
from pipecat.transcriptions.language import Language
from pipecat.services.deepgram import DeepgramSTTService
from pipecat.transports.network.fastapi_websocket import (
    FastAPIWebsocketTransport,
    FastAPIWebsocketParams,
)
from pipecat.audio.vad.silero import SileroVADAnalyzer, VADParams
from pipecat.serializers.twilio import TwilioFrameSerializer

# Other imports
from deepgram import LiveOptions

# Custom processors
from custom_pipecat.custom_processors.transcripts_processor import (
    TranscriptCaptureProcessor,
    BotBufferProcessor,
)
from custom_pipecat.custom_processors.debugging_processor import DebuggingFrameProcessor
# from custom_pipecat.custom_audiofilters.krisp_filter import KrispFilter


# Utility functions for reading parameters and handling file paths
from utils.read_params import read_params
from utils.file_path import get_file_path_from_raw
from pipecat.services.gladia import GladiaSTTService

# Load environment variables and parameters
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_PAGE_ID = os.getenv("NOTION_PAGE_ID")

load_dotenv(override=True)
params = read_params()

# Configure logging
logger.remove()  # Remove default handlers
logger.add(sys.stderr, level="DEBUG")

# Load additional environment variables
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_BOOKINGS_TABLE = os.getenv("AIRTABLE_BOOKINGS_TABLE")
NOTION_PAGE_ID = os.getenv("NOTION_PAGE_ID")
NOTION_API_KEY = os.getenv("NOTION_API_KEY")

# Import custom functions for handling various tasks
from functions import (
    find_booking,
    update_terminal,
    update_phone_number,
    transfer_call,
    whatsapp_message,
    find_booking_by_phone,
    update_eta,
    handle_get_current_time,
    handle_get_current_date,
    update_vehicle_details,
)

from functions.find_booking_by_ref import find_booking_by_ref

from functions.whatsapp_message import whatsapp_message_extension

# Define custom interruption processor
from custom_pipecat.custom_processors.interruption_processor import InterruptionFrameProcessor


# Main function to run the bot
async def run_bot(websocket_client, stream_sid, call_sid, call_info):
    logger.info(f"Starting bot for stream_sid: {stream_sid}")
    async with aiohttp.ClientSession() as session:
        try:
            transport = FastAPIWebsocketTransport(
                websocket=websocket_client,
                params=FastAPIWebsocketParams(
                    audio_out_enabled=True,
                    add_wav_header=False,
                    vad_enabled=True,
                    vad_analyzer=SileroVADAnalyzer(
                        params=VADParams(
                            confidence=0.6,
                            min_volume=0.3,
                            stop_secs=0.3,
                        )
                    ),
                    vad_audio_passthrough=True,
                    serializer=TwilioFrameSerializer(stream_sid),
                    # audio_in_filter=KrispFilter(),
                ),
            )
            logger.debug(f"Transport initialized for stream_sid: {stream_sid}")

            # Initialize OpenAI LLM service
            llm = OpenAILLMService(api_key=os.getenv("OPENAI_API_KEY"), model="gpt-4o")

            logger.debug("OpenAI LLM service initialized")

            # Register functions
            llm.register_function("find_booking", find_booking)
            llm.register_function("update_terminal", update_terminal)
            llm.register_function("update_phone_number", update_phone_number)
            llm.register_function("transfer_call", transfer_call)
            llm.register_function("whatsapp_message", whatsapp_message)
            llm.register_function("find_booking_by_phone", find_booking_by_phone)
            llm.register_function("update_eta", update_eta)
            llm.register_function("get_current_time", handle_get_current_time)
            llm.register_function("get_current_date", handle_get_current_date)
            llm.register_function("whatsapp_message_extension", whatsapp_message_extension)
            llm.register_function("update_vehicle_details", update_vehicle_details)
            llm.register_function(
                "find_booking_by_ref", find_booking_by_ref
            )  # Add find_booking_by_ref registration

            # Initialize Deepgram STT service
            stt = DeepgramSTTService(
                api_key=os.getenv("DEEPGRAM_API_KEY"),
                live_options=LiveOptions(
                    encoding="linear16",
                    model="nova-2-phonecall",
                    sample_rate=8000,
                    channels=2,
                    interim_results=True,
                    smart_format=True,
                    punctuate=True,
                    profanity_filter=True,
                    vad_events=False,
                ),
            )

            # Initialize Cartesia TTS service
            tts = CartesiaTTSService(
                api_key=os.getenv("CARTESIA_API_KEY"),
                voice_id="79a125e8-cd45-4c13-8a67-188112f4dd22",
                # output_format={"encoding": "pcm_mulaw", "sample_rate": 8000, "container": "raw"},
                text_filter=MarkdownTextFilter(),
            )

            # Initialize custom processors
            transcript_capture_processor = TranscriptCaptureProcessor()
            debugging_frame_processor = DebuggingFrameProcessor()
            bot_buffer_processor = BotBufferProcessor()

            interruption_frame_processor = InterruptionFrameProcessor()

            tools = [
                ChatCompletionToolParam(
                    type="function",
                    function={
                        "name": "find_booking_by_ref",
                        "description": "Find a booking using the booking reference number",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "booking_ref": {
                                    "type": "string",
                                    "description": "The booking reference number (e.g., GL-MAN-78961, CPD-19-581405)",
                                },
                            },
                            "required": ["booking_ref"],
                        },
                    },
                ),
                ChatCompletionToolParam(
                    type="function",
                    function={
                        "name": "find_booking",
                        "description": "Find a booking by registration number",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "registration": {
                                    "type": "string",
                                    "description": "The vehicle registration number",
                                },
                            },
                            "required": ["registration"],
                        },
                    },
                ),
                ChatCompletionToolParam(
                    type="function",
                    function={
                        "name": "update_terminal",
                        "description": "Update the terminal for a booking",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "registration": {
                                    "type": "string",
                                    "description": "The vehicle registration number",
                                },
                                "terminal": {
                                    "type": "string",
                                    "description": "The new terminal (e.g., 'Terminal 1', 'Terminal 2', 'Terminal 3')",
                                },
                            },
                            "required": ["registration", "terminal"],
                        },
                    },
                ),
                ChatCompletionToolParam(
                    type="function",
                    function={
                        "name": "update_phone_number",
                        "description": "Update the phone number for a booking",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "registration": {
                                    "type": "string",
                                    "description": "The vehicle registration number",
                                },
                                "phone_number": {
                                    "type": "string",
                                    "description": "The new phone number",
                                },
                            },
                            "required": ["registration", "phone_number"],
                        },
                    },
                ),
                ChatCompletionToolParam(
                    type="function",
                    function={
                        "name": "transfer_call",
                        "description": "Transfer the current call to a human agent",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "call_sid": {
                                    "type": "string",
                                    "description": "The unique identifier for the current call",
                                },
                            },
                            "required": ["call_sid"],
                        },
                    },
                ),
                ChatCompletionToolParam(
                    type="function",
                    function={
                        "name": "whatsapp_message",
                        "description": "Send a WhatsApp message to notify staff about a new booking",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "registration": {
                                    "type": "string",
                                    "description": "The vehicle registration number",
                                },
                                "is_drop_off": {
                                    "type": "boolean",
                                    "description": "Whether the booking is for a drop-off (true) or collection (false)",
                                },
                            },
                            "required": ["registration", "is_drop_off"],
                        },
                    },
                ),
                ChatCompletionToolParam(
                    type="function",
                    function={
                        "name": "find_booking_by_phone",
                        "description": "Find a booking using the customer's phone number",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "phone_number": {
                                    "type": "string",
                                    "description": "The customer's phone number",
                                },
                            },
                            "required": ["phone_number"],
                        },
                    },
                ),
                ChatCompletionToolParam(
                    type="function",
                    function={
                        "name": "update_eta",
                        "description": "Update the estimated time of arrival (ETA) for a booking",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "registration": {
                                    "type": "string",
                                    "description": "The vehicle registration number",
                                },
                                "customer_eta": {
                                    "type": "string",
                                    "description": "The customer's estimated time of arrival. Can be a relative time (e.g., '30 minutes' or '2 hours') or an exact time (e.g., '4:30 PM')",
                                },
                            },
                            "required": ["registration", "customer_eta"],
                        },
                    },
                ),
                ChatCompletionToolParam(
                    type="function",
                    function={
                        "name": "get_current_time",
                        "description": "Get the current time in UK timezone",
                        "parameters": {
                            "type": "object",
                            "properties": {},  # This function doesn't require any parameters
                            "required": [],
                        },
                    },
                ),
                ChatCompletionToolParam(
                    type="function",
                    function={
                        "name": "get_current_date",
                        "description": "Get the current date in UK timezone",
                        "parameters": {
                            "type": "object",
                            "properties": {},  # This function doesn't require any parameters
                            "required": [],
                        },
                    },
                ),
                ChatCompletionToolParam(
                    type="function",
                    function={
                        "name": "whatsapp_message_extension",
                        "description": "Send a WhatsApp message to notify staff about a booking that needs extension",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "booking_details": {
                                    "type": "object",
                                    "description": "The details of the expired booking",
                                },
                            },
                            "required": ["booking_details"],
                        },
                    },
                ),
                ChatCompletionToolParam(
                    type="function",
                    function={
                        "name": "update_vehicle_details",
                        "description": "Update the vehicle details for a booking",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "registration": {
                                    "type": "string",
                                    "description": "The vehicle registration number",
                                },
                                "vehicle_details": {
                                    "type": "string",
                                    "description": "The new vehicle details including make, model, and color",
                                },
                            },
                            "required": ["registration", "vehicle_details"],
                        },
                    },
                ),
            ]

            # Define initial messages for the conversation
            messages = [{"role": "system", "content": params["prompts"]["assistant_prompt"]}]

            # Add additional instruction to the system prompt
            messages[0]["content"] += (
                "\n\nImportant: After finding a booking, always check the 'dropOffStatus' for drop-offs or 'collectionStatus' for collections. If the relevant status is 'Driver Requested', inform the customer that a driver has already been requested for their booking. Ask if they're calling about a different booking or if there's anything else you can help with."
            )
            messages[0]["content"] += (
                "\n\nImportant: Ensure you look up the booking details for the customer's registration number right after saying 'I will look up your booking details'."
            )
            messages[0]["content"] += (
                "\n\nImportant: Right after you say something like 'I'll now send a message to our team to request a driver for your drop-off.' Never go silent always be pro-active. So either instantly do the function call or confirm with the customer. "
            )
            messages[0]["content"] += (
                "\n\nImportant: If the lookup fails make sure to tell the customer what you looked up so they can correct you."
            )
            messages[0]["content"] += (
                "\n\nImportant: WHEN CONFIRMING BOOKING DETAILS WITH CUSTOMER ALWAYS ENSURE YOU CONFIRM THE DATE AND TIME OF THE BOOKING, NOT JUST THE DATE"
            )
            context = OpenAILLMContext(messages, tools)
            context_aggregator = llm.create_context_aggregator(context)

            # Define the conversation pipeline
            interruption_frame_processor = InterruptionFrameProcessor()

            pipeline = Pipeline(
                [
                    transport.input(),  # Websocket input from client
                    stt,  # Speech-To-Text
                    # interruption_frame_processor,
                    context_aggregator.user(),  # User responses
                    llm,  # LLM
                    tts,  # Text-To-Speech
                    transport.output(),  # Websocket output to client
                    # bot_buffer_processor,  # Add this line
                    context_aggregator.assistant(),  # LLM responses
                    transcript_capture_processor,  # Add this line
                ]
            )

            # Create pipeline task before event handlers
            task = PipelineTask(
                pipeline,
                PipelineParams(
                    allow_interruptions=True,
                    enable_metrics=True,
                    enable_usage_metrics=True,
                    report_only_initial_ttfb=True,
                ),
            )

            # Define event handler for client connection
            @transport.event_handler("on_client_connected")
            async def on_client_connected(transport, client):
                # Set up logging for the new call
                file_path = get_file_path_from_raw(
                    call_sid, call_info.to, "logs", "call_log", "log", params
                )
                if file_path:
                    # Configure Loguru to write logs to the specified file
                    # Use a unique identifier for this handler
                    handler_id = logger.add(
                        file_path,
                        rotation="1 week",
                        retention="1 month",
                        level="DEBUG",
                        enqueue=True,
                    )
                    # Store the handler_id in the transport object for later removal
                    transport.log_handler_id = handler_id
                # Example of a log to test the configuration
                logger.info(f"New call connected. Logs are written to {file_path}")
                logger.info(f"Call from {call_info._from} to {call_info.to}")
                # Send welcome message using queue manager
                welcome_message = params["discussion"]["welcome_message"]
                # sentences_welcome_message = re.split(r"(?<=[.!?])\s+", welcome_message)

                await tts.say(welcome_message)
                messages[0]["content"] += welcome_message

            # Define event handler for client disconnection
            @transport.event_handler("on_client_disconnected")
            async def on_client_disconnected(transport, client):
                await task.queue_frames([EndFrame()])
                # Save transcript
                transcript = transcript_capture_processor.get_transcript(bot_buffer_processor)
                file_path = get_file_path_from_raw(
                    call_sid, call_info.to, "transcripts", "transcript", "txt", params
                )
                # Save transcript (only if path was created)
                if file_path:
                    with open(file_path, "w") as file:
                        file.write(transcript)
                    logger.info(f"Transcription saved in file: {file_path}")
                # Remove the logger handler
                if hasattr(transport, "log_handler_id"):
                    logger.remove(transport.log_handler_id)

            # Run the pipeline
            runner = PipelineRunner(handle_sigint=False)
            logger.info("Starting pipeline runner")
            await runner.run(task)

        except Exception as e:
            logger.exception(f"Error in run_bot: {str(e)}")
        finally:
            logger.info("Customer has ended call")
