import os
from twilio.rest import Client
from pipecat.frames.frames import EndFrame, TTSSpeakFrame, EndTaskFrame
from pipecat.processors.frame_processor import FrameDirection


async def hangup_call(function_name, tool_call_id, args, llm, context, result_callback):
    print("End call function called")
    print(f"Function name: {function_name}")
    print(f"Context: {context}")
    for key, value in args.items():
        print(f"{key}: {value}")

    await llm.push_frame(EndTaskFrame(), FrameDirection.UPSTREAM)
