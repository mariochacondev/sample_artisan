"""Audio sample generation utilities."""

from __future__ import annotations

import io
import math
import wave

DEFAULT_SAMPLE_RATE = 44_100


def generate_wave_sample(
    *,
    frequency: float = 440.0,
    duration: float = 1.0,
    waveform: str = "sine",
    amplitude: float = 0.65,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
) -> bytes:
    """Generate a mono 16-bit PCM WAV sample."""
    if frequency <= 0:
        raise ValueError("frequency must be greater than zero")
    if duration <= 0:
        raise ValueError("duration must be greater than zero")
    if not 0 < amplitude <= 1:
        raise ValueError("amplitude must be between 0 and 1")

    frame_count = int(sample_rate * duration)
    frames = bytearray()

    for index in range(frame_count):
        phase = (index * frequency / sample_rate) % 1.0
        value = _wave_value(phase, waveform)
        sample = int(value * amplitude * 32767)
        frames.extend(sample.to_bytes(2, byteorder="little", signed=True))

    output = io.BytesIO()
    with wave.open(output, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(frames)

    return output.getvalue()


def _wave_value(phase: float, waveform: str) -> float:
    match waveform:
        case "sine":
            return math.sin(2 * math.pi * phase)
        case "square":
            return 1.0 if phase < 0.5 else -1.0
        case "saw":
            return (2.0 * phase) - 1.0
        case "triangle":
            return 4.0 * abs(phase - 0.5) - 1.0
        case _:
            raise ValueError(f"unsupported waveform: {waveform}")
