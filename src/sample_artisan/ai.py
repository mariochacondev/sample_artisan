"""AI-assisted sample parameter planning."""

from __future__ import annotations

from dataclasses import asdict, fields, replace
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
        "chord": {"type": "string"},
        "osc1_level": {"type": "number", "minimum": 0, "maximum": 1},
        "osc1_octave": {"type": "integer", "minimum": -4, "maximum": 4},
        "osc1_semitone": {"type": "integer", "minimum": -24, "maximum": 24},
        "osc1_fine": {"type": "number", "minimum": -100, "maximum": 100},
        "osc2_waveform": {"type": "string", "enum": list(WAVEFORMS)},
        "osc2_ratio": {"type": "number", "minimum": 0.25, "maximum": 8},
        "osc2_level": {"type": "number", "minimum": 0, "maximum": 1},
        "osc2_octave": {"type": "integer", "minimum": -4, "maximum": 4},
        "osc2_semitone": {"type": "integer", "minimum": -24, "maximum": 24},
        "osc2_fine": {"type": "number", "minimum": -100, "maximum": 100},
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
        "character": {"type": "number", "minimum": 0, "maximum": 1},
        "drift": {"type": "number", "minimum": 0, "maximum": 1},
        "smear": {"type": "number", "minimum": 0, "maximum": 1},
        "space": {"type": "number", "minimum": 0, "maximum": 1},
        "description": {"type": "string"},
    },
    "required": [field.name for field in fields(SynthPatch) if field.name != "seed"],
}


def plan_sample_from_prompt(prompt: str, model: str | None = None) -> SynthPatch:
    """Convert a natural-language prompt into a synth patch."""
    cleaned_prompt = prompt.strip()
    if not cleaned_prompt:
        raise ValueError("prompt must not be empty")

    try:
        return plan_sample_with_ollama(cleaned_prompt, model=model)
    except RuntimeError:
        return plan_sample_locally(cleaned_prompt)


def plan_sample_locally(prompt: str) -> SynthPatch:
    """Design a basic patch without requiring Ollama."""
    lowered = prompt.lower()
    chord = _find_chord_symbol(prompt)
    engine = _local_engine(lowered, chord)
    waveform = _local_waveform(lowered, engine)
    patch = SynthPatch(
        engine=engine,
        waveform=waveform,
        frequency=_local_frequency(lowered, engine, chord),
        duration=_local_duration(lowered, engine, chord),
        amplitude=0.72 if chord else 0.68,
        attack=0.003 if engine in {"kick", "percussion"} else 0.008,
        decay=_local_decay(lowered, engine, chord),
        sustain=0.0 if engine in {"kick", "snare", "closed_hat", "open_hat", "percussion"} else 0.25,
        release=0.08 if not chord else 0.18,
        noise_mix=_local_noise_mix(lowered, engine),
        filter_cutoff=_local_filter_cutoff(lowered, engine),
        filter_mode="highpass" if engine in {"closed_hat", "open_hat"} else "lowpass",
        drive=0.24 if any(word in lowered for word in ("gritty", "dirty", "distorted", "drive")) else 0.06,
        pitch_drop=1.8 if engine == "kick" else 0.0,
        metallic=0.82 if engine in {"closed_hat", "open_hat"} else 0.0,
        bit_depth=12 if any(word in lowered for word in ("lofi", "bit", "crushed", "dirty")) else 16,
        chord=chord,
        osc1_level=0.85 if chord else 1.0,
        osc1_octave=0,
        osc1_semitone=0,
        osc1_fine=-4 if any(word in lowered for word in ("wide", "detuned", "chorus")) else 0,
        osc2_waveform=_local_osc2_waveform(lowered, waveform),
        osc2_ratio=1.0,
        osc2_level=0.38 if chord or any(word in lowered for word in ("wide", "detuned", "thick")) else 0.18,
        osc2_octave=1 if any(word in lowered for word in ("bright", "shimmer", "wide")) else 0,
        osc2_semitone=7 if any(word in lowered for word in ("fifth", "power")) else 0,
        osc2_fine=7 if any(word in lowered for word in ("wide", "detuned", "chorus")) else 0,
        noise_type="metal" if engine in {"closed_hat", "open_hat"} else "wood" if engine == "percussion" else "white",
        noise_decay=0.05 if engine == "closed_hat" else 0.5 if engine == "open_hat" else 0.08,
        filter_resonance=0.18 if chord else 0.08,
        filter_env=0.18 if engine in {"pluck", "bass", "texture"} else 0.0,
        pitch_env=0.0,
        pitch_decay=0.08,
        transient_level=0.45 if engine in {"kick", "percussion"} else 0.12 if engine == "pluck" else 0.0,
        transient_tone=3500 if engine == "pluck" else 1500,
        body_level=0.65 if engine == "percussion" else 0.0,
        body_frequency=180.0,
        body_decay=0.35,
        character=0.28 if any(word in lowered for word in ("organic", "dusty", "vintage", "real")) else 0.08,
        drift=0.18 if any(word in lowered for word in ("organic", "detuned", "vintage")) else 0.03,
        smear=0.12 if any(word in lowered for word in ("soft", "smeared", "dusty")) else 0.0,
        space=0.22 if any(word in lowered for word in ("wide", "space", "reverb", "ambient")) else 0.04,
        description=f"Local fallback patch for {prompt}",
    )
    return _polish_patch(patch)


def plan_sample_with_ollama(prompt: str, model: str | None = None) -> SynthPatch:
    """Ask a local Ollama model to design a synth patch."""
    system = (
        "You are designing one-shot synthesizer patches for a Python audio tool. "
        "Return only one JSON object. Think like a Serum/Vital sound designer "
        "building a one-shot patch from two oscillators, noise, transient, filter, "
        "pitch envelope, resonant body, and realism controls. Oscillator 1 uses "
        "waveform, osc1_level, osc1_octave, osc1_semitone, and osc1_fine. "
        "Oscillator 2 uses osc2_waveform, osc2_ratio, osc2_level, osc2_octave, "
        "osc2_semitone, and osc2_fine. If the prompt asks for a chord such as "
        "Am9, Cmaj7, Dm11, or G13, set chord to that exact chord symbol and tune "
        "the patch so the rendered audio plays the real chord tones. Leave chord "
        "empty for single-note or drum sounds. Use broad engines instead of "
        "literal instrument names: conga, bongo, tom, wood block, and hand drum "
        "-> percussion; kick or bass drum -> kick; bass or sub -> bass; pluck, "
        "mallet, kalimba -> pluck; ambience, riser, fx -> texture; "
        "snare/clap/rimshot -> snare; hihats -> closed_hat or open_hat; cymbal, "
        "crash, and ride -> open_hat. Never choose snare for conga, kick, or "
        "cymbal. Keep description concise. Use these keys when possible: "
        "engine, waveform, frequency, duration, amplitude, attack, decay, "
        "sustain, release, noise_mix, filter_cutoff, filter_mode, drive, "
        "pitch_drop, metallic, bit_depth, chord, osc1_level, osc1_octave, "
        "osc1_semitone, osc1_fine, osc2_waveform, osc2_ratio, osc2_level, "
        "osc2_octave, osc2_semitone, osc2_fine, noise_type, noise_decay, "
        "filter_resonance, filter_env, pitch_env, pitch_decay, transient_level, "
        "transient_tone, body_level, body_frequency, body_decay, character, "
        "drift, smear, space, description."
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
        timeout = float(os.getenv("OLLAMA_TIMEOUT", "6"))
        with request.urlopen(req, timeout=timeout) as response:
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
        frequency=_float_value(patch_data, "frequency"),
        duration=_float_value(patch_data, "duration"),
        amplitude=_float_value(patch_data, "amplitude"),
        attack=_float_value(patch_data, "attack"),
        decay=_float_value(patch_data, "decay"),
        sustain=_float_value(patch_data, "sustain"),
        release=_float_value(patch_data, "release"),
        noise_mix=_float_value(patch_data, "noise_mix"),
        filter_cutoff=_float_value(patch_data, "filter_cutoff"),
        filter_mode=patch_data["filter_mode"],
        drive=_float_value(patch_data, "drive"),
        pitch_drop=_float_value(patch_data, "pitch_drop"),
        metallic=_float_value(patch_data, "metallic"),
        bit_depth=_int_value(patch_data, "bit_depth"),
        chord=str(patch_data["chord"]).strip(),
        osc1_level=_float_value(patch_data, "osc1_level"),
        osc1_octave=_int_value(patch_data, "osc1_octave"),
        osc1_semitone=_int_value(patch_data, "osc1_semitone"),
        osc1_fine=_float_value(patch_data, "osc1_fine"),
        osc2_waveform=patch_data["osc2_waveform"],
        osc2_ratio=_float_value(patch_data, "osc2_ratio"),
        osc2_level=_float_value(patch_data, "osc2_level"),
        osc2_octave=_int_value(patch_data, "osc2_octave"),
        osc2_semitone=_int_value(patch_data, "osc2_semitone"),
        osc2_fine=_float_value(patch_data, "osc2_fine"),
        noise_type=patch_data["noise_type"],
        noise_decay=_float_value(patch_data, "noise_decay"),
        filter_resonance=_float_value(patch_data, "filter_resonance"),
        filter_env=_float_value(patch_data, "filter_env"),
        pitch_env=_float_value(patch_data, "pitch_env"),
        pitch_decay=_float_value(patch_data, "pitch_decay"),
        transient_level=_float_value(patch_data, "transient_level"),
        transient_tone=_float_value(patch_data, "transient_tone"),
        body_level=_float_value(patch_data, "body_level"),
        body_frequency=_float_value(patch_data, "body_frequency"),
        body_decay=_float_value(patch_data, "body_decay"),
        character=_float_value(patch_data, "character"),
        drift=_float_value(patch_data, "drift"),
        smear=_float_value(patch_data, "smear"),
        space=_float_value(patch_data, "space"),
        description=str(patch_data["description"]),
    )


def _polish_patch(patch: SynthPatch) -> SynthPatch:
    if patch.engine == "kick":
        return replace(
            patch,
            waveform="sine",
            chord="",
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
            character=_clamp(patch.character, 0.08, 0.35),
            drift=_clamp(patch.drift, 0.02, 0.22),
            smear=_clamp(patch.smear, 0.0, 0.2),
            space=_clamp(patch.space, 0.0, 0.18),
        )
    if patch.engine == "percussion":
        return replace(
            patch,
            chord="",
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
            character=_clamp(patch.character, 0.32, 0.85),
            drift=_clamp(patch.drift, 0.12, 0.55),
            smear=_clamp(patch.smear, 0.08, 0.45),
            space=_clamp(patch.space, 0.03, 0.35),
        )
    if patch.engine in {"closed_hat", "open_hat"}:
        return replace(
            patch,
            chord="",
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
            character=_clamp(patch.character, 0.18, 0.65),
            drift=_clamp(patch.drift, 0.05, 0.35),
            smear=_clamp(patch.smear, 0.03, 0.35),
            space=_clamp(patch.space, 0.04, 0.45),
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


def _find_chord_symbol(prompt: str) -> str:
    for token in prompt.replace(",", " ").split():
        cleaned = token.strip(".,;:!?()[]{}")
        if not cleaned:
            continue
        try:
            from sample_artisan.synth import _chord_intervals

            if _chord_intervals(cleaned):
                return cleaned
        except ValueError:
            continue
    return ""


def _local_engine(prompt: str, chord: str) -> str:
    if any(word in prompt for word in ("kick", "808", "bass drum", "sub hit")):
        return "kick"
    if any(word in prompt for word in ("snare", "clap", "rim")):
        return "snare"
    if any(word in prompt for word in ("closed hat", "closed hihat", "hihat", "hi-hat")):
        return "closed_hat"
    if any(word in prompt for word in ("open hat", "cymbal", "crash", "ride")):
        return "open_hat"
    if any(word in prompt for word in ("conga", "bongo", "tom", "drum", "percussion")):
        return "percussion"
    if any(word in prompt for word in ("bass", "sub", "reese")):
        return "bass"
    if chord or any(word in prompt for word in ("pluck", "keys", "chord", "stab")):
        return "pluck"
    if any(word in prompt for word in ("pad", "texture", "ambient", "riser", "fx")):
        return "texture"
    if "noise" in prompt:
        return "noise"
    return "tone"


def _local_waveform(prompt: str, engine: str) -> str:
    if "square" in prompt:
        return "square"
    if "triangle" in prompt:
        return "triangle"
    if "saw" in prompt or engine in {"bass", "pluck", "texture"}:
        return "saw"
    return "sine"


def _local_osc2_waveform(prompt: str, waveform: str) -> str:
    if "triangle" in prompt:
        return "triangle"
    if "square" in prompt:
        return "square"
    if waveform == "saw":
        return "triangle"
    return "saw"


def _local_frequency(prompt: str, engine: str, chord: str) -> float:
    if chord:
        from sample_artisan.synth import _chord_root_frequency

        return _chord_root_frequency(chord) or 220.0
    if engine == "kick":
        return 55.0
    if engine == "bass":
        return 110.0 if "sub" not in prompt else 55.0
    if engine in {"closed_hat", "open_hat"}:
        return 7800.0
    if engine == "percussion":
        return 220.0
    return 440.0


def _local_duration(prompt: str, engine: str, chord: str) -> float:
    if "long" in prompt or "sustain" in prompt:
        return 1.6 if chord else 1.2
    if "short" in prompt or "stab" in prompt:
        return 0.45 if chord else 0.18
    if engine == "closed_hat":
        return 0.08
    if engine == "open_hat":
        return 0.65
    if engine == "kick":
        return 0.42
    return 0.75 if chord else 0.4


def _local_decay(prompt: str, engine: str, chord: str) -> float:
    if "short" in prompt or "tight" in prompt:
        return 0.12
    if "long" in prompt:
        return 1.2
    if chord:
        return 0.55
    if engine == "open_hat":
        return 0.55
    if engine == "closed_hat":
        return 0.05
    return 0.25


def _local_noise_mix(prompt: str, engine: str) -> float:
    if engine in {"closed_hat", "open_hat", "snare", "noise"}:
        return 0.85
    if "noisy" in prompt or "dusty" in prompt:
        return 0.18
    if engine == "percussion":
        return 0.12
    return 0.0


def _local_filter_cutoff(prompt: str, engine: str) -> float:
    if "dark" in prompt or "warm" in prompt:
        return 2400.0
    if "bright" in prompt:
        return 11000.0
    if engine == "bass":
        return 1800.0
    if engine in {"closed_hat", "open_hat"}:
        return 7000.0
    return 6500.0


def _float_value(data: dict[str, object], key: str) -> float:
    default = getattr(SynthPatch(), key)
    try:
        return float(data[key])
    except (KeyError, TypeError, ValueError):
        return float(default)


def _int_value(data: dict[str, object], key: str) -> int:
    default = getattr(SynthPatch(), key)
    try:
        return int(float(data[key]))
    except (KeyError, TypeError, ValueError):
        return int(default)


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))
