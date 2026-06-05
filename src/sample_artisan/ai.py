"""AI-assisted sample parameter planning."""

from __future__ import annotations

from dataclasses import asdict, replace
import json
import os
from urllib import error, request

from sample_artisan.synth import ENGINES, NOISE_TYPES, WAVEFORMS, SynthPatch

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
        "osc2_waveform": {"type": "string", "enum": list(WAVEFORMS)},
        "osc2_ratio": {"type": "number", "minimum": 0.25, "maximum": 8},
        "osc2_level": {"type": "number", "minimum": 0, "maximum": 1},
        "noise_type": {"type": "string", "enum": list(NOISE_TYPES)},
        "noise_decay": {"type": "number", "minimum": 0.005, "maximum": 3},
        "filter_resonance": {"type": "number", "minimum": 0, "maximum": 1},
        "filter_env": {"type": "number", "minimum": -1, "maximum": 1},
        "pitch_env": {"type": "number", "minimum": -1200, "maximum": 1200},
        "pitch_decay": {"type": "number", "minimum": 0.005, "maximum": 2},
        "transient_level": {"type": "number", "minimum": 0, "maximum": 1},
        "transient_tone": {"type": "number", "minimum": 80, "maximum": 12000},
        "body_level": {"type": "number", "minimum": 0, "maximum": 1},
        "body_frequency": {"type": "number", "minimum": 35, "maximum": 2000},
        "body_decay": {"type": "number", "minimum": 0.02, "maximum": 4},
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
        "osc2_waveform",
        "osc2_ratio",
        "osc2_level",
        "noise_type",
        "noise_decay",
        "filter_resonance",
        "filter_env",
        "pitch_env",
        "pitch_decay",
        "transient_level",
        "transient_tone",
        "body_level",
        "body_frequency",
        "body_decay",
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
        "Return only one JSON object. Think like a Serum/Vital sound "
        "designer building a one-shot patch from oscillators, noise, transient, "
        "filter, pitch envelope, and resonant body. Use broad engines instead "
        "of literal instrument names: conga, bongo, tom, wood block, and hand "
        "drum -> percussion with body_level, body_frequency, transient_level, "
        "wood noise, and short-to-medium decay; kick or bass drum -> kick; "
        "bass or sub -> bass; pluck, mallet, kalimba -> pluck; ambience, riser, "
        "fx -> texture; snare/clap/rimshot -> snare; hihats -> closed_hat or "
        "open_hat; cymbal, crash, and ride -> open_hat with metal noise, highpass "
        "filtering, high metallic amount, and longer decay. Never choose snare "
        "for conga, kick, or cymbal. Tune body_frequency "
        "to the perceived note/body of the sound. Keep description concise. "
        "Use these keys when possible: engine, waveform, frequency, duration, "
        "amplitude, attack, decay, sustain, release, noise_mix, filter_cutoff, "
        "filter_mode, drive, pitch_drop, metallic, bit_depth, osc2_waveform, "
        "osc2_ratio, osc2_level, noise_type, noise_decay, filter_resonance, "
        "filter_env, pitch_env, pitch_decay, transient_level, transient_tone, "
        "body_level, body_frequency, body_decay, description."
    )
    body = {
        "model": model or os.getenv("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL),
        "prompt": f"{system}\n\nSound prompt: {prompt}",
        "stream": False,
        "format": "json",
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
        with request.urlopen(req, timeout=45) as response:
            raw = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace").strip()
        message = detail or str(exc)
        raise RuntimeError(f"Ollama request failed: {message}") from exc
    except (OSError, error.URLError, json.JSONDecodeError) as exc:
        raise RuntimeError("Ollama is not available") from exc

    response_text = str(raw.get("response", "")).strip()
    if not response_text:
        raise RuntimeError("Ollama returned an empty response")
    return _polish_patch(_parse_patch(response_text))


def _parse_patch(raw_text: str) -> SynthPatch:
    data = _load_patch_json(raw_text)
    patch_data = asdict(SynthPatch())
    patch_data.update(data)
    patch_data["engine"] = _normalize_engine(str(patch_data["engine"]))
    patch_data["waveform"] = _normalize_choice(
        str(patch_data["waveform"]), WAVEFORMS, "sine"
    )
    patch_data["osc2_waveform"] = _normalize_choice(
        str(patch_data["osc2_waveform"]), WAVEFORMS, "sine"
    )
    patch_data["noise_type"] = _normalize_choice(
        str(patch_data["noise_type"]), NOISE_TYPES, "white"
    )
    patch_data["filter_mode"] = _normalize_choice(
        str(patch_data["filter_mode"]), ("lowpass", "highpass"), "lowpass"
    )
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
        osc2_waveform=patch_data["osc2_waveform"],
        osc2_ratio=float(patch_data["osc2_ratio"]),
        osc2_level=float(patch_data["osc2_level"]),
        noise_type=patch_data["noise_type"],
        noise_decay=float(patch_data["noise_decay"]),
        filter_resonance=float(patch_data["filter_resonance"]),
        filter_env=float(patch_data["filter_env"]),
        pitch_env=float(patch_data["pitch_env"]),
        pitch_decay=float(patch_data["pitch_decay"]),
        transient_level=float(patch_data["transient_level"]),
        transient_tone=float(patch_data["transient_tone"]),
        body_level=float(patch_data["body_level"]),
        body_frequency=float(patch_data["body_frequency"]),
        body_decay=float(patch_data["body_decay"]),
        description=patch_data["description"],
    )


def _polish_patch(patch: SynthPatch) -> SynthPatch:
    if patch.engine == "kick":
        return replace(
            patch,
            waveform="sine",
            frequency=_clamp(patch.frequency, 35.0, 90.0),
            duration=_clamp(patch.duration, 0.18, 0.85),
            attack=_clamp(patch.attack, 0.001, 0.008),
            decay=_clamp(patch.decay, 0.12, 0.6),
            sustain=0.0,
            release=_clamp(patch.release, 0.03, 0.18),
            noise_mix=_clamp(patch.noise_mix, 0.0, 0.18),
            filter_cutoff=_clamp(patch.filter_cutoff, 180.0, 1_800.0),
            filter_mode="lowpass",
            pitch_drop=max(patch.pitch_drop, 1.6),
            metallic=0.0,
        )
    if patch.engine == "percussion":
        return replace(
            patch,
            frequency=_clamp(patch.frequency, 120.0, 520.0),
            duration=_clamp(patch.duration, 0.16, 1.4),
            attack=_clamp(patch.attack, 0.001, 0.015),
            decay=_clamp(patch.decay, 0.08, 0.9),
            sustain=0.0,
            noise_mix=_clamp(patch.noise_mix, 0.02, 0.35),
            noise_type=patch.noise_type if patch.noise_type != "metal" else "wood",
            filter_cutoff=_clamp(patch.filter_cutoff, 500.0, 6_000.0),
            filter_mode="lowpass",
            pitch_drop=_clamp(patch.pitch_drop, 0.0, 0.9),
            transient_level=_clamp(patch.transient_level, 0.12, 0.75),
            body_level=_clamp(patch.body_level, 0.35, 1.0),
            body_frequency=_clamp(patch.body_frequency, 120.0, 520.0),
            body_decay=_clamp(patch.body_decay, 0.12, 1.2),
            metallic=_clamp(patch.metallic, 0.0, 0.2),
        )
    if patch.engine in {"closed_hat", "open_hat"}:
        return replace(
            patch,
            frequency=_clamp(patch.frequency, 2_500.0, 11_000.0),
            duration=_clamp(
                patch.duration,
                0.04 if patch.engine == "closed_hat" else 0.18,
                1.8,
            ),
            attack=_clamp(patch.attack, 0.0, 0.01),
            decay=_clamp(
                patch.decay,
                0.03 if patch.engine == "closed_hat" else 0.18,
                1.5,
            ),
            sustain=0.0,
            noise_mix=_clamp(patch.noise_mix, 0.55, 1.0),
            noise_type="metal",
            filter_cutoff=_clamp(patch.filter_cutoff, 4_000.0, 14_000.0),
            filter_mode="highpass",
            metallic=_clamp(patch.metallic, 0.55, 1.0),
            body_level=0.0,
        )
    return patch


def _load_patch_json(raw_text: str) -> dict[str, object]:
    try:
        loaded = json.loads(raw_text)
    except json.JSONDecodeError:
        start = raw_text.find("{")
        end = raw_text.rfind("}")
        if start < 0 or end <= start:
            raise
        loaded = json.loads(raw_text[start : end + 1])
    if not isinstance(loaded, dict):
        raise ValueError("AI response must be a JSON object")
    return loaded


def _normalize_engine(engine: str) -> str:
    normalized = engine.strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "cymbal": "open_hat",
        "crash": "open_hat",
        "crash_cymbal": "open_hat",
        "ride": "open_hat",
        "ride_cymbal": "open_hat",
        "hat": "closed_hat",
        "hi_hat": "closed_hat",
        "hihat": "closed_hat",
        "closed_hihat": "closed_hat",
        "open_hihat": "open_hat",
        "conga": "percussion",
        "bongo": "percussion",
        "tom": "percussion",
        "wood_block": "percussion",
        "sub": "bass",
        "sub_bass": "bass",
        "mallet": "pluck",
        "kalimba": "pluck",
        "pad": "texture",
        "riser": "texture",
        "fx": "texture",
    }
    normalized = aliases.get(normalized, normalized)
    return normalized if normalized in ENGINES else "tone"


def _normalize_choice(value: str, choices: tuple[str, ...], default: str) -> str:
    normalized = value.strip().lower().replace("-", "_").replace(" ", "_")
    return normalized if normalized in choices else default


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))
