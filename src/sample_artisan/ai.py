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

    provider = os.getenv("SAMPLE_ARTISAN_AI", "ollama").lower()
    if provider == "local":
        return plan_sample_locally(cleaned_prompt)

    try:
        return plan_sample_with_ollama(cleaned_prompt, model=model)
    except RuntimeError:
        return plan_sample_locally(cleaned_prompt)


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


def plan_sample_locally(prompt: str) -> SynthPatch:
    """Use free local prompt rules to choose a synth patch."""
    words = prompt.lower()
    if _has_any(words, "closed hihat", "closed hi-hat", "closed hat", "tight hat"):
        return SynthPatch(
            engine="closed_hat",
            waveform="square",
            frequency=7_500,
            duration=0.08,
            amplitude=0.75,
            attack=0.001,
            decay=0.055,
            sustain=0.0,
            release=0.015,
            noise_mix=0.95,
            filter_cutoff=7_000,
            filter_mode="highpass",
            drive=0.25,
            metallic=0.9,
            bit_depth=12,
            description="Local patch: tight metallic closed hi-hat.",
        )
    if _has_any(words, "open hihat", "open hi-hat", "open hat"):
        return SynthPatch(
            engine="open_hat",
            waveform="square",
            frequency=6_500,
            duration=0.45,
            amplitude=0.7,
            attack=0.001,
            decay=0.32,
            sustain=0.0,
            release=0.08,
            noise_mix=0.9,
            filter_cutoff=6_000,
            filter_mode="highpass",
            drive=0.18,
            metallic=0.85,
            bit_depth=12,
            description="Local patch: airy open hi-hat.",
        )
    if _has_any(words, "snare", "rim"):
        return SynthPatch(
            engine="snare",
            waveform="triangle",
            frequency=190,
            duration=0.22,
            amplitude=0.85,
            attack=0.002,
            decay=0.16,
            sustain=0.0,
            release=0.04,
            noise_mix=0.72,
            filter_cutoff=2_400,
            filter_mode="highpass",
            drive=0.35,
            metallic=0.2,
            bit_depth=14,
            description="Local patch: crisp noise snare.",
        )
    if _has_any(words, "kick", "bd", "bass drum"):
        return SynthPatch(
            engine="kick",
            waveform="sine",
            frequency=55,
            duration=0.42,
            amplitude=0.95,
            attack=0.001,
            decay=0.26,
            sustain=0.0,
            release=0.08,
            noise_mix=0.05,
            filter_cutoff=1_600,
            filter_mode="lowpass",
            drive=0.45,
            pitch_drop=3.0,
            bit_depth=16,
            description="Local patch: punchy pitch-drop kick.",
        )

    return _melodic_patch(words)


def _melodic_patch(words: str) -> SynthPatch:
    waveform = "sine"
    if _has_any(words, "gritty", "harsh", "distorted", "buzz", "lead"):
        waveform = "saw"
    elif _has_any(words, "bass", "8-bit", "chip", "chiptune", "square", "punch"):
        waveform = "square"
    elif _has_any(words, "triangle", "mellow", "round", "smooth"):
        waveform = "triangle"

    frequency = 440.0
    if _has_any(words, "sub", "deep", "low", "bass"):
        frequency = 110.0
    elif _has_any(words, "high", "bright", "sparkle", "glassy", "bell"):
        frequency = 880.0

    duration = 0.35 if _has_any(words, "short", "stab", "hit", "pluck") else 1.0
    if _has_any(words, "long", "pad", "drone", "swell", "sustain"):
        duration = 2.4

    return SynthPatch(
        engine="tone",
        waveform=waveform,
        frequency=frequency,
        duration=duration,
        amplitude=0.75 if _has_any(words, "loud", "hard", "punchy") else 0.6,
        attack=0.002 if _has_any(words, "pluck", "stab", "hit") else 0.03,
        decay=0.18 if _has_any(words, "pluck", "stab", "hit") else 0.5,
        sustain=0.0 if _has_any(words, "pluck", "stab", "hit") else 0.35,
        release=0.08,
        noise_mix=0.12 if _has_any(words, "air", "breath", "noisy") else 0.0,
        filter_cutoff=8_000 if _has_any(words, "bright", "glassy") else 4_000,
        filter_mode="lowpass",
        drive=0.3 if _has_any(words, "gritty", "distorted", "dirty") else 0.0,
        metallic=0.35 if _has_any(words, "bell", "metal", "glassy") else 0.0,
        bit_depth=8 if _has_any(words, "8-bit", "lofi", "chip") else 16,
        description=f"Local patch: {waveform} {frequency:.0f} Hz tone.",
    )


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


def _has_any(words: str, *needles: str) -> bool:
    return any(needle in words for needle in needles)
