import asyncio
import base64
import json

async def convert_and_send_to_twilio(mp3_path, ws,stream_sid):
    """Convert MP3 to mulaw using ffmpeg and send to Twilio"""

    # ffmpeg command: MP3 -> mulaw 8kHz mono
    ffmpeg_cmd = [
        'ffmpeg', '-i', mp3_path,
        '-ar', '8000',  # 8kHz sample rate
        '-ac', '1',  # mono
        '-f', 'mulaw',  # mulaw format
        '-'  # output to stdout
    ]

    process = await asyncio.create_subprocess_exec(
        *ffmpeg_cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL
    )

    # Read all mulaw data
    mulaw_audio, _ = await process.communicate()
    await send_mulaw_to_twilio(mulaw_audio,ws,stream_sid)

async def send_mulaw_to_twilio(audio,ws,stream_sid):
    CHUNK_SIZE = 160

    for i in range(0, len(audio), CHUNK_SIZE):
        chunk = audio[i:i + CHUNK_SIZE]

        payload = base64.b64encode(chunk).decode("utf-8")

        msg = {
            "event": "media",
            "streamSid": stream_sid,
            "media": {
                "payload": payload
            }
        }

        await ws.send_text(json.dumps(msg))
        await asyncio.sleep(0.02)