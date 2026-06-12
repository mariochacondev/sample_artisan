"""AI-assisted sample parameter planning."""

from __future__ import annotations

from dataclasses import asdict, fields, replace
import json
import os
from urllib import error, request

from sample_artisan.synth import (
    ENGINES,
    NOISE_TYPES,
    WAVEFORMS,
    SynthPatch,
    _chord_intervals,
)

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
DEFAULT_OLLAMA_MODEL = "llama3.2"
DEFAULT_OLLAMA_TIMEOUT = 120
DEFAULT_OLLAMA_NUM_PREDICT = 900
DEFAULT_OLLAMA_KEEP_ALIVE = "10m"

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
        "oscillator_unison": {"type": "integer", "minimum": 1, "maximum": 8},
        "oscillator_detune": {"type": "number", "minimum": 0, "maximum": 50},
        "oscillator_shape": {"type": "number", "minimum": 0, "maximum": 1},
        "pulse_width": {"type": "number", "minimum": 0.05, "maximum": 0.95},
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
        "chorus": {"type": "number", "minimum": 0, "maximum": 1},
        "tremolo_rate": {"type": "number", "minimum": 0, "maximum": 30},
        "tremolo_depth": {"type": "number", "minimum": 0, "maximum": 1},
        "output_gain": {"type": "number", "minimum": 0, "maximum": 2},
        "output_headroom": {"type": "number", "minimum": 0.1, "maximum": 1},
        "description": {"type": "string"},
    },
    "required": [field.name for field in fields(SynthPatch) if field.name != "seed"],
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
        "You are the patch designer for sample_artisan, a one-shot sample "
        "generator. Return only one compact JSON object. Use the user's prompt "
        "to choose the sound source and parameters. Do not use generic defaults "
        "unless the prompt is generic. Available engines: tone for simple tonal "
        "one-shots, kick for bass drums, snare for snares/claps/rimshots, "
        "closed_hat for tight hats, open_hat for open hats/cymbals/crashes/rides, "
        "noise for noise hits, percussion for congas/bongos/toms/hand drums, "
        "bass for bass/sub/808 hits, keys for piano/upright piano/electric piano/"
        "keyboard chords and soft key hits, pluck for plucked synths/mallets/"
        "kalimba and chord stabs, texture for ambience/risers/fx. "
        "Use only these keys when needed: engine, waveform, frequency, duration, "
        "amplitude, attack, decay, sustain, release, noise_mix, filter_cutoff, "
        "filter_mode, drive, pitch_drop, metallic, bit_depth, chord, osc1_level, "
        "osc1_octave, osc1_semitone, osc1_fine, osc2_waveform, osc2_ratio, "
        "osc2_level, osc2_octave, osc2_semitone, osc2_fine, oscillator_unison, "
        "oscillator_detune, oscillator_shape, pulse_width, noise_type, "
        "noise_decay, filter_resonance, filter_env, pitch_env, pitch_decay, "
        "transient_level, transient_tone, body_level, body_frequency, body_decay, "
        "character, drift, smear, space, chorus, tremolo_rate, tremolo_depth, "
        "output_gain, output_headroom, description. "
        "All time values are seconds, not milliseconds. Good one-shot durations "
        "are usually 0.03 to 1.5. Do not output huge values like 100 or 200 for "
        "decay, release, noise_decay, pitch_decay, or body_decay. "
        "Use oscillator_unison for thicker synths, supersaws, wide plucks, pads, "
        "and rich chord stabs. Use 1 for clean/simple/realistic sounds, 2 to 4 "
        "for mild width, and 5 to 8 for dense supersaw-like stacks. Use "
        "oscillator_detune in cents: 0 for clean sounds, 4 to 12 for subtle "
        "movement, 12 to 25 for wide synths, and avoid high detune for realistic "
        "piano unless the user asks for chorus or detuned character. "
        "Use pulse_width for square/pulse sounds: 0.5 is balanced, lower or higher "
        "values make thinner nasal pulse waves. Use oscillator_shape to morph or "
        "bend oscillator tone: 0 clean, 0.2 to 0.5 more character, above 0.6 for "
        "folded or rounded synthetic color. Use chorus for Juno pads, Rhodes, wide "
        "keys, and lush synths. Use tremolo_rate and tremolo_depth for Rhodes, "
        "Wurlitzer, vibey keys, and rhythmic motion. Use output_gain for final "
        "level and output_headroom from 0.75 to 0.92 to prevent clipping. "
        "Use chord only for real chord symbols requested by the user, such as "
        "Am9, Cmaj7, Dm11, or G13. For drums, claps, snares, hats, cymbals, "
        "percussion, bass hits, single notes, or textures, set chord to an empty "
        "string or omit it. Never put instrument names in chord. "
        "For piano or upright piano prompts, use engine keys. Keep amplitude "
        "around 0.35 to 0.58 for chords, drive near 0, bit_depth 16, noise_mix "
        "below 0.08, metallic below 0.25, lowpass filtering around 3000 to 9000, "
        "attack 0.002 to 0.02, decay 0.7 to 2.8, sustain 0 to 0.25, release "
        "0.15 to 0.8, transient_level 0.08 to 0.35, body_level 0.12 to 0.45, "
        "oscillator_unison 1 to 2, oscillator_detune 0 to 5, oscillator_shape "
        "0 to 0.25, pulse_width 0.5, chorus 0 to 0.18, tremolo_depth 0, "
        "character for harmonics, drift for natural tuning, smear for softer felt, "
        "and space for room. Softer piano should reduce filter_cutoff and transient; "
        "more impact should add character/body, not clipping or high drive. "
        "For Rhodes or electric piano, use engine keys, triangle or sine, moderate "
        "metallic and character for tine/bell partials, body_level for cabinet, "
        "chorus 0.18 to 0.45, tremolo_rate 3 to 7, tremolo_depth 0.15 to 0.45, "
        "low drive 0.05 to 0.18, and controlled headroom. "
        "Examples: prompt 'clap' -> engine snare, waveform square or noise-like, "
        "duration 0.12, attack 0.001, decay 0.12, sustain 0, release 0.04, "
        "noise_mix 0.8, filter_mode highpass, filter_cutoff 2500, transient_level "
        "0.6, transient_tone 3500, chord empty. Prompt 'closed hihat' -> engine "
        "closed_hat, short duration, high noise_mix, highpass filtering, metallic "
        "tone. Prompt 'wide detuned Am9 pluck' -> engine pluck, chord Am9, saw "
        "or triangle oscillators, oscillator_unison 4, oscillator_detune 14, "
        "oscillator_shape 0.25, short attack, musical decay. Prompt 'upright "
        "piano Fm9 soft but harmonic' -> engine keys, chord Fm9, sine or triangle, "
        "duration 1.4, amplitude 0.45, attack 0.008, decay 1.6, sustain 0.08, "
        "release 0.45, filter_mode lowpass, filter_cutoff 5200, drive 0, "
        "oscillator_unison 1, oscillator_detune 0, oscillator_shape 0.12, "
        "pulse_width 0.5, transient_level 0.18, transient_tone 2600, "
        "body_level 0.28, body_decay 1.6, character 0.45, drift 0.16, "
        "smear 0.35, space 0.22, chorus 0.08, output_headroom 0.86."
    )
    model_name = model or os.getenv("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL)
    url = os.getenv("OLLAMA_URL", OLLAMA_URL)
    timeout = float(os.getenv("OLLAMA_TIMEOUT", str(DEFAULT_OLLAMA_TIMEOUT)))
    num_predict = int(os.getenv("OLLAMA_NUM_PREDICT", str(DEFAULT_OLLAMA_NUM_PREDICT)))
    keep_alive = os.getenv("OLLAMA_KEEP_ALIVE", DEFAULT_OLLAMA_KEEP_ALIVE)
    body = {
        "model": model_name,
        "prompt": f"{system}\n\nSound prompt: {prompt}",
        "stream": False,
        "format": PATCH_SCHEMA,
        "keep_alive": keep_alive,
        "options": {"temperature": 0.1, "num_predict": num_predict},
    }
    payload = json.dumps(body).encode("utf-8")
    req = request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=timeout) as response:
            response_body = response.read().decode("utf-8")
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace").strip()
        message = detail or exc.reason or str(exc)
        raise RuntimeError(
            f"Ollama request failed at {url} with model {model_name}: "
            f"HTTP {exc.code} {message}"
        ) from exc
    except TimeoutError as exc:
        raise RuntimeError(
            f"Ollama timed out after {timeout:g}s at {url} "
            f"with model {model_name}"
        ) from exc
    except (OSError, error.URLError) as exc:
        detail = getattr(exc, "reason", exc)
        raise RuntimeError(
            f"Ollama is not reachable at {url} with model {model_name}: {detail}"
        ) from exc

    try:
        raw = json.loads(response_body)
    except json.JSONDecodeError as exc:
        snippet = response_body[:240].replace("\n", " ")
        raise RuntimeError(
            f"Ollama returned non-JSON from {url} with model {model_name}: {snippet}"
        ) from exc

    response_text = str(raw.get("response", "")).strip()
    if not response_text:
        raise RuntimeError(
            f"Ollama returned an empty response from {url} with model {model_name}"
        )
    try:
        return _parse_patch(response_text)
    except (json.JSONDecodeError, ValueError) as exc:
        snippet = response_text[:240].replace("\n", " ")
        raise RuntimeError(
            f"Ollama returned an invalid patch JSON with model {model_name}: {snippet}"
        ) from exc


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
        chord=_normalize_chord(str(patch_data["chord"])),
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
        oscillator_unison=_int_value(patch_data, "oscillator_unison"),
        oscillator_detune=_float_value(patch_data, "oscillator_detune"),
        oscillator_shape=_float_value(patch_data, "oscillator_shape"),
        pulse_width=_float_value(patch_data, "pulse_width"),
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
        chorus=_float_value(patch_data, "chorus"),
        tremolo_rate=_float_value(patch_data, "tremolo_rate"),
        tremolo_depth=_float_value(patch_data, "tremolo_depth"),
        output_gain=_float_value(patch_data, "output_gain"),
        output_headroom=_float_value(patch_data, "output_headroom"),
        description=str(patch_data["description"]),
    )


def _polish_patch(patch: SynthPatch) -> SynthPatch:
    if patch.engine in {"kick", "snare", "closed_hat", "open_hat", "noise", "percussion"}:
        patch = replace(patch, chord="")

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
            character=_clamp(patch.character, 0.08, 0.35),
            drift=_clamp(patch.drift, 0.02, 0.22),
            smear=_clamp(patch.smear, 0.0, 0.2),
            space=_clamp(patch.space, 0.0, 0.18),
            output_headroom=_clamp(patch.output_headroom, 0.78, 0.92),
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
            character=_clamp(patch.character, 0.32, 0.85),
            drift=_clamp(patch.drift, 0.12, 0.55),
            smear=_clamp(patch.smear, 0.08, 0.45),
            space=_clamp(patch.space, 0.03, 0.35),
            output_headroom=_clamp(patch.output_headroom, 0.78, 0.92),
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
            character=_clamp(patch.character, 0.18, 0.65),
            drift=_clamp(patch.drift, 0.05, 0.35),
            smear=_clamp(patch.smear, 0.03, 0.35),
            space=_clamp(patch.space, 0.04, 0.45),
            output_headroom=_clamp(patch.output_headroom, 0.78, 0.92),
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
        "clap": "snare",
        "calp": "snare",
        "rimshot": "snare",
        "conga": "percussion",
        "bongo": "percussion",
        "tom": "percussion",
        "wood_block": "percussion",
        "sub": "bass",
        "sub_bass": "bass",
        "piano": "keys",
        "upright": "keys",
        "upright_piano": "keys",
        "rhodes": "keys",
        "wurlitzer": "keys",
        "electric_piano": "keys",
        "epiano": "keys",
        "keyboard": "keys",
        "key": "keys",
        "juno": "texture",
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


def _normalize_chord(value: str) -> str:
    chord = value.strip()
    if not chord or chord.lower() in {"none", "null", "false", "n/a", "no chord"}:
        return ""
    return chord if _chord_intervals(chord) is not None else ""


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
