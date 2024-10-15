import asyncio

async def test_tts_service():
    tts_service = CartesiaTTSService(
                api_key=os.getenv("CARTESIA_API_KEY"),
                voice_id="641a6ee5-9427-47de-8f81-c92025db1a4b",
        output_format={"encoding": "pcm_s16le", "sample_rate": 16000, "container": "raw"},
    )
    audio_data = await tts_service.say("Test message")
    if audio_data is None:
        print("TTS service returned None")
    else:
        print(f"TTS service returned {len(audio_data)} bytes of audio data")

asyncio.run(test_tts_service())
