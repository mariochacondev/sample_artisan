"""AI-assisted sample parameter planning."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass


DEFAULT_AI_MODEL = "gpt-5.4-mini"
WAVEFORMS = ("sine", "square", "saw", "triangle")


@dataclass(frozen=True)
class SamplePlan:
    waveform: str
    frequency: float
    duration: float
    amplitude: float
    description: str


def plan_sample_from_prompt(prompt: str, model: str | None = None) -> SamplePlan:
    """Convert a natural-language prompt into synthesizer parameters."""
    cleaned_prompt = prompt.strip()
    if not cleaned_prompt:
        raise ValueError("prompt must not be empty")

    if not os.getenv("OPENAI_API_KEY"):
        return plan_sample_locally(cleaned_prompt)

    try:
        from openai import OpenAI
    except ImportError as error:
        raise RuntimeError("Install sample-artisan[ai] to use OpenAI prompts") from error

    client = OpenAI()
    response = client.responses.create(
        model=model or os.getenv("OPENAI_MODEL", DEFAULT_AI_MODEL),
        instructions=(
            "You translate sound-design prompts into safe parameters for a simple "
            "mono WAV synthesizer. Choose values that fit the requested mood. "
            "Use only these waveforms: sine, square, saw, triangle."
        ),
        input=cleaned_prompt,
        text={
            "format": {
                "type": "json_schema",
                "name": "sample_plan",
                "strict": True,
                "schema": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "waveform": {
                            "type": "string",
                            "enum": ["sine", "square", "saw", "triangle"],
                        },
                        "frequency": {
                            "type": "number",
                            "minimum": 80,
                            "maximum": 1200,
                        },
                        "duration": {
                            "type": "number",
                            "minimum": 0.1,
                            "maximum": 3,
                        },
                        "amplitude": {
                            "type": "number",
                            "minimum": 0.1,
                            "maximum": 1,
                        },
                        "description": {
                            "type": "string",
                            "maxLength": 140,
                        },
                    },
                    "required": [
                        "waveform",
                        "frequency",
                        "duration",
                        "amplitude",
                        "description",
                    ],
                },
            }
        },
    )

    return _parse_plan(response.output_text)


def plan_sample_locally(prompt: str) -> SamplePlan:
    """Use free local prompt rules to choose sample parameters."""
    words = prompt.lower()
    waveform = _choose_waveform(words)
    frequency = _choose_frequency(words)
    duration = _choose_duration(words)
    amplitude = _choose_amplitude(words)
    description = (
        f"Local plan: {waveform} wave, {frequency:.0f} Hz, "
        f"{duration:.1f} s, {int(amplitude * 100)}% amplitude."
    )

    return SamplePlan(
        waveform=waveform,
        frequency=frequency,
        duration=duration,
        amplitude=amplitude,
        description=description,
    )


def _parse_plan(raw_text: str) -> SamplePlan:
    data = json.loads(raw_text)
    return SamplePlan(
        waveform=data["waveform"],
        frequency=float(data["frequency"]),
        duration=float(data["duration"]),
        amplitude=float(data["amplitude"]),
        description=data["description"],
    )


def _choose_waveform(words: str) -> str:
    if _has_any(words, "gritty", "harsh", "distorted", "buzz", "buzzing", "lead"):
        return "saw"
    if _has_any(words, "bass", "8-bit", "chip", "chiptune", "square", "punch"):
        return "square"
    if _has_any(words, "pluck", "bell", "glassy", "soft", "warm", "pure"):
        return "sine"
    if _has_any(words, "triangle", "mellow", "round", "smooth"):
        return "triangle"
    return "sine"


def _choose_frequency(words: str) -> float:
    frequency = 440.0
    if _has_any(words, "sub", "deep", "low", "bass", "kick"):
        frequency = 110.0
    elif _has_any(words, "mid", "vocal", "body"):
        frequency = 330.0
    elif _has_any(words, "high", "bright", "sparkle", "glassy", "bell"):
        frequency = 880.0

    if _has_any(words, "very low", "floor", "rumble"):
        frequency *= 0.7
    if _has_any(words, "very high", "piercing", "tiny"):
        frequency *= 1.25

    return _clamp(frequency, 80.0, 1200.0)


def _choose_duration(words: str) -> float:
    if _has_any(words, "short", "stab", "hit", "pluck", "click", "kick"):
        return 0.35
    if _has_any(words, "long", "pad", "drone", "swell", "sustain"):
        return 2.4
    if _has_any(words, "medium", "note", "tone"):
        return 1.0
    return 0.8


def _choose_amplitude(words: str) -> float:
    if _has_any(words, "quiet", "soft", "gentle", "distant"):
        return 0.4
    if _has_any(words, "loud", "hard", "punchy", "aggressive", "impact"):
        return 0.85
    return 0.65


def _has_any(words: str, *needles: str) -> bool:
    return any(needle in words for needle in needles)


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))
