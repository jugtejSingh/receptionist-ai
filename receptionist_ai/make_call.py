import json
import base64
import asyncio
import sys

from fastapi import FastAPI, Response, WebSocket
from langchain_core.messages import SystemMessage
from twilio.twiml.voice_response import VoiceResponse

from receptionist_ai.prompts import SYSTEM_PROMPT
from receptionist_ai.stt import DeepgramTranscriber

app = FastAPI()

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

messages_state = [SystemMessage(content=str(SYSTEM_PROMPT))]
@app.post("/voice")
def twilio_starting_connection():
    twiml = VoiceResponse()
    twiml.connect().stream(
        url="wss://unsprouted-starlike-roni.ngrok-free.dev/twilio/stream",
        track="inbound_track",
    )

    return Response(content=twiml.to_xml(), media_type="application/xml")

@app.websocket("/twilio/stream")
async def twilio_stream(ws: WebSocket):
    await ws.accept()
    stream_sid = None

    # Initialize and start Deepgram
    dg_transcriber = DeepgramTranscriber()
    await dg_transcriber.start()

    # Start FFmpeg as a middleman (mulaw 8k -> linear16 16k)
    ffmpeg_cmd = [
        'ffmpeg', '-f', 'mulaw', '-ar', '8000', '-i', '-',
        '-f', 's16le', '-ar', '16000', '-ac', '1', '-'
    ]
    process = await asyncio.create_subprocess_exec(
        *ffmpeg_cmd,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
    )

    # Background task to read from FFmpeg and send to Deepgram
    async def relay_to_dg():
        try:
            while True:
                data = await process.stdout.read(2048)
                if not data: break
                await dg_transcriber.send_audio(data)
        except Exception as e:
            if "OK" not in str(e):
                print(f"FFmpeg Relay Error: {e}")

    asyncio.create_task(relay_to_dg())

    try:
        while True:
            msg = await ws.receive_text()
            data = json.loads(msg)

            if data['event'] == 'start':
                stream_sid = data['start']['streamSid']
                dg_transcriber.ws = ws
                dg_transcriber.stream_sid = stream_sid
                print("🎧 Stream started:", stream_sid)

            if data['event'] == 'media':
                # 1. Decode Twilio's base64
                audio_bytes = base64.b64decode(data['media']['payload'])
                # 2. Feed it into FFmpeg's stdin
                process.stdin.write(audio_bytes)
                await process.stdin.drain()

            elif data['event'] == 'stop':
                print("we outie")
                break
    except Exception as e:
        print(f"WebSocket Loop Error: {e}")
    finally:
        await dg_transcriber.stop()
        process.terminate()
        print("🛑 Connection Closed")