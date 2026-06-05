"""Audio sample generation utilities."""

from __future__ import annotations

from dataclasses import dataclass
import io
import math
import random
import wave

DEFAULT_SAMPLE_RATE = 44_100
WAVEFORMS = ("sine", "square", "saw", "triangle")
NOISE_TYPES = ("white", "dark", "bright", "wood", "metal")
ENGINES = (
    "tone",
    "kick",
    "snare",
    "closed_hat",
    "open_hat",
    "noise",
    "percussion",
    "bass",
    "pluck",
    "texture",
)


@dataclass(frozen=True)
class SynthPatch:
    engine: str = "tone"
    waveform: str = "sine"
    frequency: float = 440.0
    duration: float = 1.0
    amplitude: float = 0.65
    attack: float = 0.005
    decay: float = 0.25
    sustain: float = 0.0
    release: float = 0.08
    noise_mix: float = 0.0
    filter_cutoff: float = 12_000.0
    filter_mode: str = "lowpass"
    drive: float = 0.0
    pitch_drop: float = 0.0
    metallic: float = 0.0
    bit_depth: int = 16
    seed: int = 7
    description: str = "Manual patch"
    osc2_waveform: str = "sine"
    osc2_ratio: float = 1.0
    osc2_level: float = 0.0
    noise_type: str = "white"
    noise_decay: float = 0.08
    filter_resonance: float = 0.0
    filter_env: float = 0.0
    pitch_env: float = 0.0
    pitch_decay: float = 0.08
    transient_level: float = 0.0
    transient_tone: float = 1_500.0
    body_level: float = 0.0
    body_frequency: float = 180.0
    body_decay: float = 0.35


def generate_wave_sample(
    *,
    frequency: float = 440.0,
    duration: float = 1.0,
    waveform: str = "sine",
    amplitude: float = 0.65,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    engine: str = "tone",
    attack: float = 0.005,
    decay: float = 0.25,
    sustain: float = 0.0,
    release: float = 0.08,
    noise_mix: float = 0.0,
    filter_cutoff: float = 12_000.0,
    filter_mode: str = "lowpass",
    drive: float = 0.0,
    pitch_drop: float = 0.0,
    metallic: float = 0.0,
    bit_depth: int = 16,
    seed: int = 7,
    osc2_waveform: str = "sine",
    osc2_ratio: float = 1.0,
    osc2_level: float = 0.0,
    noise_type: str = "white",
    noise_decay: float = 0.08,
    filter_resonance: float = 0.0,
    filter_env: float = 0.0,
    pitch_env: float = 0.0,
    pitch_decay: float = 0.08,
    transient_level: float = 0.0,
    transient_tone: float = 1_500.0,
    body_level: float = 0.0,
    body_frequency: float = 180.0,
    body_decay: float = 0.35,
) -> bytes:
    """Generate a mono 16-bit PCM WAV sample."""
    patch = SynthPatch(
        engine=engine,
        waveform=waveform,
        frequency=frequency,
        duration=duration,
        amplitude=amplitude,
        attack=attack,
        decay=decay,
        sustain=sustain,
        release=release,
        noise_mix=noise_mix,
        filter_cutoff=filter_cutoff,
        filter_mode=filter_mode,
        drive=drive,
        pitch_drop=pitch_drop,
        metallic=metallic,
        bit_depth=bit_depth,
        seed=seed,
        osc2_waveform=osc2_waveform,
        osc2_ratio=osc2_ratio,
        osc2_level=osc2_level,
        noise_type=noise_type,
        noise_decay=noise_decay,
        filter_resonance=filter_resonance,
        filter_env=filter_env,
        pitch_env=pitch_env,
        pitch_decay=pitch_decay,
        transient_level=transient_level,
        transient_tone=transient_tone,
        body_level=body_level,
        body_frequency=body_frequency,
        body_decay=body_decay,
    )
    return render_patch(patch, sample_rate=sample_rate)


def render_patch(patch: SynthPatch, sample_rate: int = DEFAULT_SAMPLE_RATE) -> bytes:
    """Render a synth patch to WAV bytes."""
    _validate_patch(patch)
    rng = random.Random(patch.seed)
    frame_count = max(1, int(sample_rate * patch.duration))
    values: list[float] = []
    phase = 0.0

    for index in range(frame_count):
        t = index / sample_rate
        progress = index / frame_count
        frequency = _frequency_at(patch, t, progress)
        phase = (phase + frequency / sample_rate) % 1.0
        tone = _engine_value(patch, phase, t, rng)
        noise = _noise_value(patch, rng)
        noise *= _noise_envelope(t, patch)
        transient = _transient_value(patch, t, rng)
        body = _body_value(patch, t)
        mixed = (tone * (1.0 - patch.noise_mix)) + (noise * patch.noise_mix)
        mixed += transient + body
        mixed *= _envelope(t, patch)
        mixed = _apply_drive(mixed, patch.drive)
        mixed = _apply_bit_depth(mixed, patch.bit_depth)
        values.append(mixed * patch.amplitude)

    values = _apply_filter(values, patch, sample_rate)
    frames = bytearray()
    for value in values:
        sample = int(_clamp(value, -1.0, 1.0) * 32767)
        frames.extend(sample.to_bytes(2, byteorder="little", signed=True))

    output = io.BytesIO()
    with wave.open(output, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(frames)

    return output.getvalue()


def _validate_patch(patch: SynthPatch) -> None:
    if patch.engine not in ENGINES:
        raise ValueError(f"unsupported engine: {patch.engine}")
    if patch.waveform not in WAVEFORMS:
        raise ValueError(f"unsupported waveform: {patch.waveform}")
    if patch.osc2_waveform not in WAVEFORMS:
        raise ValueError(f"unsupported osc2_waveform: {patch.osc2_waveform}")
    if patch.noise_type not in NOISE_TYPES:
        raise ValueError(f"unsupported noise_type: {patch.noise_type}")
    if patch.frequency <= 0:
        raise ValueError("frequency must be greater than zero")
    if patch.duration <= 0:
        raise ValueError("duration must be greater than zero")
    if not 0 < patch.amplitude <= 1:
        raise ValueError("amplitude must be between 0 and 1")
    if patch.filter_mode not in {"lowpass", "highpass"}:
        raise ValueError("filter_mode must be lowpass or highpass")


def _frequency_at(patch: SynthPatch, t: float, progress: float) -> float:
    pitch_env = patch.pitch_env * math.exp(-t / max(patch.pitch_decay, 0.001))
    base_frequency = patch.frequency + pitch_env
    if patch.pitch_drop <= 0:
        return max(20.0, base_frequency)
    if patch.engine == "kick":
        return base_frequency * (1.0 + (patch.pitch_drop * math.exp(-progress * 18.0)))
    return base_frequency + (base_frequency * patch.pitch_drop * (1.0 - progress) ** 2)


def _engine_value(patch: SynthPatch, phase: float, t: float, rng: random.Random) -> float:
    match patch.engine:
        case "kick":
            body = math.sin(2 * math.pi * phase)
            click = math.exp(-t * 260.0) * _wave_value((phase * 6.0) % 1.0, "triangle")
            return (body * 0.92) + (click * 0.18)
        case "snare":
            body = math.sin(2 * math.pi * phase) * 0.35
            return body + (rng.uniform(-1.0, 1.0) * 0.65)
        case "closed_hat" | "open_hat":
            metal = _metallic_cluster(t, patch.frequency, patch.metallic)
            return (metal * 0.55) + (rng.uniform(-1.0, 1.0) * 0.45)
        case "noise":
            return rng.uniform(-1.0, 1.0)
        case "percussion":
            tone = math.sin(2 * math.pi * phase) * 0.35
            return tone
        case "bass":
            sub = math.sin(2 * math.pi * phase)
            edge = _wave_value(phase, patch.waveform) * 0.25
            return (sub * 0.75) + edge
        case "pluck":
            main = _wave_value(phase, patch.waveform)
            harmonic = _wave_value((phase * max(0.1, patch.osc2_ratio)) % 1.0, patch.osc2_waveform)
            return (main * (1.0 - patch.osc2_level)) + (harmonic * patch.osc2_level)
        case "texture":
            harmonic = _metallic_cluster(t, patch.frequency, patch.metallic)
            return (_wave_value(phase, patch.waveform) * 0.35) + (harmonic * 0.65)
        case _:
            main = _wave_value(phase, patch.waveform)
            harmonic = _wave_value((phase * max(0.1, patch.osc2_ratio)) % 1.0, patch.osc2_waveform)
            return (main * (1.0 - patch.osc2_level)) + (harmonic * patch.osc2_level)


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


def _noise_value(patch: SynthPatch, rng: random.Random) -> float:
    raw = rng.uniform(-1.0, 1.0)
    match patch.noise_type:
        case "dark":
            return raw * 0.45
        case "bright":
            return raw if rng.random() > 0.35 else -raw
        case "wood":
            return (raw * 0.55) + (rng.uniform(-0.35, 0.35) * 0.45)
        case "metal":
            return raw * (1.0 if rng.random() > 0.55 else -0.6)
    if patch.engine in {"snare", "closed_hat", "open_hat", "noise"}:
        return raw
    return raw * 0.35


def _noise_envelope(t: float, patch: SynthPatch) -> float:
    return math.exp(-t / max(patch.noise_decay, 0.001))


def _transient_value(patch: SynthPatch, t: float, rng: random.Random) -> float:
    if patch.transient_level <= 0:
        return 0.0
    click = math.sin(2 * math.pi * patch.transient_tone * t)
    snap = rng.uniform(-1.0, 1.0) * 0.35
    return (click + snap) * patch.transient_level * math.exp(-t * 240.0)


def _body_value(patch: SynthPatch, t: float) -> float:
    if patch.body_level <= 0:
        return 0.0
    fundamental = math.sin(2 * math.pi * patch.body_frequency * t)
    overtone = math.sin(2 * math.pi * patch.body_frequency * 1.52 * t) * 0.35
    return (fundamental + overtone) * patch.body_level * math.exp(-t / max(patch.body_decay, 0.001))


def _metallic_cluster(t: float, frequency: float, metallic: float) -> float:
    ratios = (1.0, 1.41, 1.73, 2.11, 2.71, 3.19)
    amount = 0.35 + (metallic * 0.65)
    total = 0.0
    for ratio in ratios:
        total += math.sin(2 * math.pi * frequency * ratio * t)
    return (total / len(ratios)) * amount


def _envelope(t: float, patch: SynthPatch) -> float:
    if patch.engine == "kick":
        if t < patch.attack:
            return t / max(patch.attack, 0.0001)
        return math.exp(-(t - patch.attack) / max(patch.decay, 0.0001))

    if t < patch.attack:
        return t / max(patch.attack, 0.0001)
    elapsed = t - patch.attack
    decay = max(patch.decay, 0.0001)
    if elapsed < decay:
        return patch.sustain + ((1.0 - patch.sustain) * (1.0 - (elapsed / decay)))
    release_start = max(0.0, patch.duration - patch.release)
    if t >= release_start:
        return patch.sustain * (1.0 - ((t - release_start) / max(patch.release, 0.0001)))
    return patch.sustain


def _apply_drive(value: float, drive: float) -> float:
    if drive <= 0:
        return value
    gain = 1.0 + (drive * 8.0)
    return math.tanh(value * gain)


def _apply_bit_depth(value: float, bit_depth: int) -> float:
    if bit_depth >= 16:
        return value
    steps = max(2, 2 ** bit_depth)
    return round(value * steps) / steps


def _apply_filter(values: list[float], patch: SynthPatch, sample_rate: int) -> list[float]:
    cutoff = _clamp(patch.filter_cutoff, 40.0, sample_rate / 2)
    rc = 1.0 / (2 * math.pi * cutoff)
    dt = 1.0 / sample_rate
    alpha = dt / (rc + dt)
    low = 0.0
    filtered: list[float] = []
    for value in values:
        low += alpha * (value - low)
        filtered.append(low if patch.filter_mode == "lowpass" else value - low)
    return filtered


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))
