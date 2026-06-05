"""AI-assisted sample parameter planning."""

from __future__ import annotations

from dataclasses import asdict
import json
import os
from urllib import error, request

from sample_artisan.synth import ENGINES, WAVEFORMS, SynthPatch

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
DEFAULT_OLLAMA_MODEL = "llama3.2"

PATCH_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "engine": {"type": "string", "enum": list(ENGINES)},
        "waveform": {"type": "string", "enum": list(WAVEFORMS)},
        "frequency": {"type": "number", "minimum": 40, "maximum": 4000},
        "duration": {"type": "number", "minimum": 0.03, "maximum": 6},
        "amplitude": {"type": "number", "minimum": 0.05, "maximum": 1},
        "attack": {"type": "number", "minimum": 0.0, "maximum": 2},
        "decay": {"type": "number", "minimum": 0.01, "maximum": 5},
        "sustain": {"type": "number", "minimum": 0, "maximum": 1},
        "release": {"type": "number", "minimum": 0.0, "maximum": 2},
        "noise_mix": {"type": "number", "minimum": 0, "maximum": 1},
        "filter_cutoff": {"type": "number", "minimum": 80, "maximum": 18_000},
        "filter_mode": {"type": "string", "enum": ["lowpass", "highpass"]},
        "drive": {"type": "number", "minimum": 0, "maximum": 1},
        "pitch_drop": {"type": "number", "minimum": 0, "maximum": 4},
        "metallic": {"type": "number", "minimum": 0, "maximum": 1},
        "bit_depth": {"type": "integer", "minimum": 4, "maximum": 16},
        "description": {"type": "string"},
    },
    "required": [
        "engine",
        "waveform",
        "frequency",
        "duration",
        "amplitude",
        "attack",
        "decay",
        "sustain",
        "release",
        "noise_mix",
        "filter_cutoff",
        "filter_mode",
        "drive",
        "pitch_drop",
        "metallic",
        "bit_depth",
        "description",
    ],
}


def plan_sample_from_prompt(prompt: str, model: str | None = None) -> SynthPatch:
    """Convert a natural-language prompt into a synth patch."""
    cleaned_prompt = prompt.strip()
    if not cleaned_prompt:
        raise ValueError("prompt must not be empty")

    return plan_sample_with_ollama(cleaned_prompt, model=model)


def plan_sample_with_ollama(prompt: str, model: str | None = None) -> SynthPatch:
    """Ask a local Ollama model to design a synth patch."""
    system = (
        "You are designing one-shot synthesizer patches for a Python audio tool. "
        "Return only JSON matching the schema. Prefer engines over generic waves: "
        "closed hihat -> closed_hat with highpass noise, very short decay, high "
        "metallic; kick -> kick with low frequency and pitch_drop; snare -> snare "
        "with noise and short decay; bass -> tone or kick with low frequency."
    )
    body = {
        "model": model or os.getenv("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL),
        "prompt": f"{system}\n\nSound prompt: {prompt}",
        "stream": False,
        "format": PATCH_SCHEMA,
        "options": {"temperature": 0.1},
    }
    payload = json.dumps(body).encode("utf-8")
    req = request.Request(
        os.getenv("OLLAMA_URL", OLLAMA_URL),
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=15) as response:
            raw = json.loads(response.read().decode("utf-8"))
    except (OSError, error.URLError, json.JSONDecodeError) as exc:
        raise RuntimeError("Ollama is not available") from exc

    return _parse_patch(raw.get("response", "{}"))


def _parse_patch(raw_text: str) -> SynthPatch:
    data = json.loads(raw_text)
    patch_data = asdict(SynthPatch())
    patch_data.update(data)
    return SynthPatch(
        engine=patch_data["engine"],
        waveform=patch_data["waveform"],
        frequency=float(patch_data["frequency"]),
        duration=float(patch_data["duration"]),
        amplitude=float(patch_data["amplitude"]),
        attack=float(patch_data["attack"]),
        decay=float(patch_data["decay"]),
        sustain=float(patch_data["sustain"]),
        release=float(patch_data["release"]),
        noise_mix=float(patch_data["noise_mix"]),
        filter_cutoff=float(patch_data["filter_cutoff"]),
        filter_mode=patch_data["filter_mode"],
        drive=float(patch_data["drive"]),
        pitch_drop=float(patch_data["pitch_drop"]),
        metallic=float(patch_data["metallic"]),
        bit_depth=int(patch_data["bit_depth"]),
        description=patch_data["description"],
    )
