import audioop
import wave
import io


def mulaw_to_wav(mulaw_bytes: bytes) -> bytes:
    """
    Convert 8kHz μ-law audio to WAV PCM16
    """
    pcm = audioop.ulaw2lin(mulaw_bytes, 2)

    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(8000)
        wf.writeframes(pcm)

    return buffer.getvalue()
