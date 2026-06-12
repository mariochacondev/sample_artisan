"""Audio sample generation utilities."""

from __future__ import annotations

from dataclasses import dataclass
import io
import math
import random
import re
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
    "keys",
    "pluck",
    "texture",
)
TONAL_ENGINES = {"tone", "bass", "keys", "pluck", "texture"}

NOTE_OFFSETS = {
    "C": 0,
    "C#": 1,
    "DB": 1,
    "D": 2,
    "D#": 3,
    "EB": 3,
    "E": 4,
    "F": 5,
    "F#": 6,
    "GB": 6,
    "G": 7,
    "G#": 8,
    "AB": 8,
    "A": 9,
    "A#": 10,
    "BB": 10,
    "B": 11,
}


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
    chord: str = ""
    osc1_level: float = 1.0
    osc1_octave: int = 0
    osc1_semitone: int = 0
    osc1_fine: float = 0.0
    osc2_waveform: str = "sine"
    osc2_ratio: float = 1.0
    osc2_level: float = 0.0
    osc2_octave: int = 0
    osc2_semitone: int = 0
    osc2_fine: float = 0.0
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
    character: float = 0.0
    drift: float = 0.0
    smear: float = 0.0
    space: float = 0.0


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
    chord: str = "",
    osc1_level: float = 1.0,
    osc1_octave: int = 0,
    osc1_semitone: int = 0,
    osc1_fine: float = 0.0,
    osc2_waveform: str = "sine",
    osc2_ratio: float = 1.0,
    osc2_level: float = 0.0,
    osc2_octave: int = 0,
    osc2_semitone: int = 0,
    osc2_fine: float = 0.0,
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
    character: float = 0.0,
    drift: float = 0.0,
    smear: float = 0.0,
    space: float = 0.0,
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
        chord=chord,
        osc1_level=osc1_level,
        osc1_octave=osc1_octave,
        osc1_semitone=osc1_semitone,
        osc1_fine=osc1_fine,
        osc2_waveform=osc2_waveform,
        osc2_ratio=osc2_ratio,
        osc2_level=osc2_level,
        osc2_octave=osc2_octave,
        osc2_semitone=osc2_semitone,
        osc2_fine=osc2_fine,
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
        character=character,
        drift=drift,
        smear=smear,
        space=space,
    )
    return render_patch(patch, sample_rate=sample_rate)


def render_patch(patch: SynthPatch, sample_rate: int = DEFAULT_SAMPLE_RATE) -> bytes:
    """Render a synth patch to WAV bytes."""
    _validate_patch(patch)
    rng = random.Random(patch.seed)
    frame_count = max(1, int(sample_rate * patch.duration))
    values: list[float] = []
    phase = 0.0
    drift_wander = 0.0
    chord_frequencies = _chord_frequencies(patch)
    source_excitation = _source_excitation(patch)

    for index in range(frame_count):
        t = index / sample_rate
        progress = index / frame_count
        drift_wander = (drift_wander * 0.992) + rng.uniform(-0.008, 0.008)
        frequency = _frequency_at(patch, patch.frequency, t, progress)
        frequency *= _drift_multiplier(patch, t, drift_wander)
        phase_jitter = rng.uniform(-0.00002, 0.00002) * patch.character
        phase = (phase + frequency / sample_rate + phase_jitter) % 1.0
        tone = (
            _chord_stack_value(patch, chord_frequencies, t, progress, rng)
            if chord_frequencies
            else _engine_value(patch, phase, frequency, t, rng)
        )
        noise = _noise_value(patch, rng)
        noise *= _noise_envelope(t, patch)
        transient = 0.0 if patch.engine == "keys" else _transient_value(patch, t, rng)
        body = 0.0 if patch.engine == "keys" else _body_value(patch, t)
        mixed = (tone * (1.0 - patch.noise_mix)) + (noise * patch.noise_mix)
        mixed += (transient + body) * source_excitation
        mixed *= _character_gain(patch, t, rng)
        mixed += _surface_noise(patch, t, rng)
        mixed *= _envelope(t, patch)
        mixed = _apply_drive(mixed, patch.drive)
        mixed = _apply_bit_depth(mixed, patch.bit_depth)
        values.append(mixed * patch.amplitude)

    values = _apply_filter(values, patch, sample_rate)
    values = _apply_space(values, patch, sample_rate)
    values = _apply_output_headroom(values)
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
    if patch.chord and _chord_intervals(patch.chord) is None:
        raise ValueError(f"unsupported chord: {patch.chord}")


def _frequency_at(
    patch: SynthPatch, base_frequency: float, t: float, progress: float
) -> float:
    pitch_env = patch.pitch_env * math.exp(-t / max(patch.pitch_decay, 0.001))
    frequency = base_frequency * (2 ** (pitch_env / 1200.0))
    if patch.pitch_drop <= 0:
        return max(20.0, frequency)
    if patch.engine == "kick":
        return frequency * (1.0 + (patch.pitch_drop * math.exp(-progress * 18.0)))
    return frequency + (frequency * patch.pitch_drop * (1.0 - progress) ** 2)


def _engine_value(
    patch: SynthPatch, phase: float, frequency: float, t: float, rng: random.Random
) -> float:
    match patch.engine:
        case "kick":
            body = math.sin(2 * math.pi * phase)
            click = math.exp(-t * 260.0) * _wave_value((phase * 6.0) % 1.0, "triangle")
            return (body * 0.92) + (click * 0.18)
        case "snare":
            body = math.sin(2 * math.pi * phase) * 0.35
            return body + (rng.uniform(-1.0, 1.0) * 0.65)
        case "closed_hat" | "open_hat":
            metal = _metallic_cluster(t, frequency, patch.metallic)
            return (metal * 0.55) + (rng.uniform(-1.0, 1.0) * 0.45)
        case "noise":
            return rng.uniform(-1.0, 1.0)
        case "percussion":
            return math.sin(2 * math.pi * phase) * 0.35
        case "bass":
            source_level = _source_level(patch)
            sub = math.sin(2 * math.pi * phase) * source_level
            edge = _oscillator_stack_value(patch, frequency, t) * 0.35
            return (sub * 0.65) + edge
        case "keys":
            return _keys_value(patch, frequency, t, rng)
        case "texture":
            source_level = _source_level(patch)
            harmonic = _metallic_cluster(t, frequency, patch.metallic) * source_level
            return (_oscillator_stack_value(patch, frequency, t) * 0.35) + (
                harmonic * 0.65
            )
        case _:
            return _oscillator_stack_value(patch, frequency, t)


def _oscillator_stack_value(patch: SynthPatch, frequency: float, t: float) -> float:
    osc1_frequency = _tuned_frequency(
        frequency, patch.osc1_octave, patch.osc1_semitone, patch.osc1_fine
    )
    osc2_frequency = _tuned_frequency(
        frequency * max(0.1, patch.osc2_ratio),
        patch.osc2_octave,
        patch.osc2_semitone,
        patch.osc2_fine,
    )
    osc1 = _wave_value((osc1_frequency * t) % 1.0, patch.waveform) * patch.osc1_level
    osc2 = _wave_value((osc2_frequency * t) % 1.0, patch.osc2_waveform) * patch.osc2_level
    total_level = max(0.001, patch.osc1_level + patch.osc2_level)
    return (osc1 + osc2) / total_level


def _source_level(patch: SynthPatch) -> float:
    return _clamp(patch.osc1_level + patch.osc2_level, 0.0, 1.0)


def _source_excitation(patch: SynthPatch) -> float:
    return _source_level(patch) if patch.engine in TONAL_ENGINES else 1.0


def _keys_value(patch: SynthPatch, frequency: float, t: float, rng: random.Random) -> float:
    osc1_level = _clamp(patch.osc1_level, 0.0, 1.0)
    osc2_level = _clamp(patch.osc2_level, 0.0, 1.0)
    total_level = osc1_level + osc2_level
    if total_level <= 0:
        return 0.0

    osc1_frequency = _tuned_frequency(
        frequency, patch.osc1_octave, patch.osc1_semitone, patch.osc1_fine
    )
    osc2_frequency = _tuned_frequency(
        frequency * max(0.1, patch.osc2_ratio),
        patch.osc2_octave,
        patch.osc2_semitone,
        patch.osc2_fine,
    )
    osc1 = _keys_string_value(patch, osc1_frequency, t, patch.waveform)
    osc2 = _keys_string_value(patch, osc2_frequency, t, patch.osc2_waveform)
    strings = ((osc1 * osc1_level) + (osc2 * osc2_level)) / total_level
    excitation = _clamp(total_level, 0.0, 1.0)

    hammer_tone = patch.transient_tone if patch.transient_tone > 80 else frequency * 8.0
    hammer = math.sin(2 * math.pi * hammer_tone * t)
    hammer += rng.uniform(-0.6, 0.6) * (0.35 + (patch.character * 0.3))
    hammer *= patch.transient_level * excitation * math.exp(-t * 95.0 / (1.0 + patch.smear * 1.8))
    soundboard = math.sin(2 * math.pi * frequency * 0.5 * t) * patch.body_level
    soundboard *= excitation * math.exp(-t / max(patch.body_decay, 0.08))
    return strings + (hammer * 0.18) + (soundboard * 0.18)


def _keys_string_value(patch: SynthPatch, frequency: float, t: float, waveform: str) -> float:
    brightness = _clamp(0.22 + (patch.character * 0.55) + (patch.metallic * 0.25), 0.05, 1.0)
    damping = 1.0 + (patch.smear * 1.8)
    partials = (
        (1.0, 1.0, 0.55),
        (2.01, 0.46, 1.05),
        (3.02, 0.24 + (brightness * 0.12), 1.55),
        (4.07, 0.14 + (brightness * 0.10), 2.15),
        (5.12, 0.09 + (brightness * 0.08), 2.8),
        (6.21, 0.05 + (brightness * 0.06), 3.6),
    )
    total = 0.0
    total_weight = 0.0
    for ratio, weight, decay_rate in partials:
        inharmonicity = 1.0 + (patch.character * ratio * ratio * 0.0008)
        partial_frequency = frequency * ratio * inharmonicity
        decay = math.exp(-t * decay_rate / damping)
        total += _wave_value((partial_frequency * t) % 1.0, waveform) * weight * decay
        total_weight += weight
    return total / max(total_weight, 0.001)


def _chord_stack_value(
    patch: SynthPatch,
    chord_frequencies: tuple[float, ...],
    t: float,
    progress: float,
    rng: random.Random,
) -> float:
    if not chord_frequencies:
        return 0.0
    total = 0.0
    for frequency in chord_frequencies:
        voiced = _frequency_at(patch, frequency, t, progress)
        total += _engine_value(patch, (voiced * t) % 1.0, voiced, t, rng)
    return total / len(chord_frequencies)


def _tuned_frequency(
    frequency: float, octave: int, semitone: int, fine_cents: float
) -> float:
    cents = (octave * 1200) + (semitone * 100) + fine_cents
    return max(20.0, frequency * (2 ** (cents / 1200.0)))


def _chord_frequencies(patch: SynthPatch) -> tuple[float, ...]:
    intervals = _chord_intervals(patch.chord)
    root = _chord_root_frequency(patch.chord)
    if not intervals or root is None:
        return ()
    return tuple(root * (2 ** (interval / 12.0)) for interval in intervals)


def _chord_root_frequency(chord: str) -> float | None:
    parsed = _parse_chord(chord)
    if parsed is None:
        return None
    note, octave = parsed
    semitone = NOTE_OFFSETS[note]
    if octave is None:
        octave = 3 if semitone >= NOTE_OFFSETS["A"] else 4
    midi_note = (octave + 1) * 12 + semitone
    return 440.0 * (2 ** ((midi_note - 69) / 12.0))


def _chord_intervals(chord: str) -> tuple[int, ...] | None:
    parsed = _parse_chord(chord)
    if parsed is None:
        return None
    symbol = _quality_symbol(chord)
    if symbol in {"", "maj", "major"}:
        return (0, 4, 7)
    if symbol in {"m", "min", "minor"}:
        return (0, 3, 7)
    if symbol in {"5", "power"}:
        return (0, 7)
    if symbol in {"6"}:
        return (0, 4, 7, 9)
    if symbol in {"m6", "min6"}:
        return (0, 3, 7, 9)
    if symbol in {"7", "dom7"}:
        return (0, 4, 7, 10)
    if symbol in {"maj7", "ma7", "major7"}:
        return (0, 4, 7, 11)
    if symbol in {"m7", "min7", "minor7"}:
        return (0, 3, 7, 10)
    if symbol in {"mmaj7", "mmaj", "minmaj7"}:
        return (0, 3, 7, 11)
    if symbol in {"dim", "dim7"}:
        return (0, 3, 6, 9 if symbol == "dim7" else 6)
    if symbol in {"aug", "+"}:
        return (0, 4, 8)
    if symbol in {"sus2"}:
        return (0, 2, 7)
    if symbol in {"sus4", "sus"}:
        return (0, 5, 7)
    if symbol in {"9"}:
        return (0, 4, 7, 10, 14)
    if symbol in {"maj9", "ma9", "major9"}:
        return (0, 4, 7, 11, 14)
    if symbol in {"m9", "min9", "minor9"}:
        return (0, 3, 7, 10, 14)
    if symbol in {"11"}:
        return (0, 4, 7, 10, 14, 17)
    if symbol in {"m11", "min11", "minor11"}:
        return (0, 3, 7, 10, 14, 17)
    if symbol in {"13"}:
        return (0, 4, 7, 10, 14, 21)
    if symbol in {"m13", "min13", "minor13"}:
        return (0, 3, 7, 10, 14, 21)
    return None


def _parse_chord(chord: str) -> tuple[str, int | None] | None:
    match = re.match(r"^\s*([A-Ga-g])([#bB]?)", chord)
    if not match:
        return None
    note = f"{match.group(1).upper()}{match.group(2).upper()}"
    if note not in NOTE_OFFSETS:
        return None
    return note, None


def _quality_symbol(chord: str) -> str:
    match = re.match(r"^\s*[A-Ga-g][#bB]?\s*(.*)$", chord)
    if not match:
        return ""
    return (
        match.group(1)
        .strip()
        .lower()
        .replace("minor", "min")
        .replace("major", "maj")
        .replace(" ", "")
    )


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
    click_tone = patch.transient_tone * (1.0 - (patch.smear * 0.28))
    click = math.sin(2 * math.pi * click_tone * t)
    snap = rng.uniform(-1.0, 1.0) * (0.35 + (patch.character * 0.2))
    decay_rate = 240.0 / (1.0 + (patch.smear * 5.0))
    return (click + snap) * patch.transient_level * math.exp(-t * decay_rate)


def _body_value(patch: SynthPatch, t: float) -> float:
    if patch.body_level <= 0:
        return 0.0
    fundamental = math.sin(2 * math.pi * patch.body_frequency * t)
    overtone = math.sin(2 * math.pi * patch.body_frequency * 1.52 * t) * 0.35
    shell = math.sin(2 * math.pi * patch.body_frequency * 2.17 * t) * patch.character * 0.22
    membrane = math.sin(2 * math.pi * patch.body_frequency * 0.51 * t) * patch.smear * 0.18
    return (
        (fundamental + overtone + shell + membrane)
        * patch.body_level
        * math.exp(-t / max(patch.body_decay, 0.001))
    )


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
    steps = max(2, 2**bit_depth)
    return round(value * steps) / steps


def _drift_multiplier(patch: SynthPatch, t: float, wander: float) -> float:
    if patch.drift <= 0:
        return 1.0
    slow = math.sin(2 * math.pi * 1.7 * t)
    fast = math.sin((2 * math.pi * 4.3 * t) + 0.6) * 0.45
    cents = patch.drift * ((slow + fast) * 4.0 + (wander * 18.0))
    return 2 ** (cents / 1200.0)


def _character_gain(patch: SynthPatch, t: float, rng: random.Random) -> float:
    if patch.character <= 0:
        return 1.0
    slow = math.sin((2 * math.pi * 2.3 * t) + 0.3) * 0.025
    micro = rng.uniform(-0.018, 0.018)
    return max(0.0, 1.0 + (patch.character * (slow + micro)))


def _surface_noise(patch: SynthPatch, t: float, rng: random.Random) -> float:
    if patch.character <= 0:
        return 0.0
    amount = patch.character * 0.012
    if patch.engine in {"percussion", "snare", "closed_hat", "open_hat"}:
        amount *= 1.8
    amount *= _source_excitation(patch)
    return rng.uniform(-amount, amount) * math.exp(-t / max(patch.duration, 0.001))


def _apply_space(values: list[float], patch: SynthPatch, sample_rate: int) -> list[float]:
    if patch.space <= 0:
        return values
    first_delay = max(1, int(sample_rate * (0.011 + (patch.space * 0.018))))
    second_delay = max(1, int(sample_rate * (0.027 + (patch.space * 0.035))))
    first_gain = 0.08 + (patch.space * 0.18)
    second_gain = 0.04 + (patch.space * 0.12)
    damping = 1.0 - (patch.space * 0.18)
    spaced = values[:]
    for index, value in enumerate(values):
        if index >= first_delay:
            spaced[index] += values[index - first_delay] * first_gain
        if index >= second_delay:
            spaced[index] += values[index - second_delay] * second_gain
        spaced[index] *= damping
        spaced[index] += value * (1.0 - damping)
    return spaced


def _apply_filter(values: list[float], patch: SynthPatch, sample_rate: int) -> list[float]:
    dt = 1.0 / sample_rate
    low = 0.0
    band = 0.0
    filtered: list[float] = []
    frame_count = max(1, len(values))
    for index, value in enumerate(values):
        progress = index / frame_count
        cutoff = _filter_cutoff_at(patch, progress, sample_rate)
        rc = 1.0 / (2 * math.pi * cutoff)
        alpha = dt / (rc + dt)
        low += alpha * (value - low)
        high = value - low
        band += alpha * (high - band)
        resonance = band * patch.filter_resonance * 1.8
        filtered.append(
            (low + resonance)
            if patch.filter_mode == "lowpass"
            else (high + resonance)
        )
    return filtered


def _apply_output_headroom(values: list[float], headroom: float = 0.92) -> list[float]:
    peak = max((abs(value) for value in values), default=0.0)
    if peak <= headroom:
        return values
    gain = headroom / peak
    return [value * gain for value in values]


def _filter_cutoff_at(patch: SynthPatch, progress: float, sample_rate: int) -> float:
    env_amount = patch.filter_env * (1.0 - progress) ** 2
    cutoff = patch.filter_cutoff * (2.0**env_amount)
    return _clamp(cutoff, 40.0, sample_rate / 2)


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))
