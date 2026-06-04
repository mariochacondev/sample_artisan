"""AI-assisted sample parameter planning."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass


DEFAULT_AI_MODEL = "gpt-5.4-mini"


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
        raise RuntimeError("OPENAI_API_KEY is required for AI prompt generation")

    try:
        from openai import OpenAI
    except ImportError as error:
        raise RuntimeError("Install the openai package to use AI prompts") from error

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


def _parse_plan(raw_text: str) -> SamplePlan:
    data = json.loads(raw_text)
    return SamplePlan(
        waveform=data["waveform"],
        frequency=float(data["frequency"]),
        duration=float(data["duration"]),
        amplitude=float(data["amplitude"]),
        description=data["description"],
    )
