import io
import wave

from sample_artisan import generate_wave_sample
from sample_artisan.synth import _wave_value


def _peak(sample: bytes) -> float:
    with wave.open(io.BytesIO(sample), "rb") as wav_file:
        frames = wav_file.readframes(wav_file.getnframes())
    values = [
        abs(int.from_bytes(frames[index : index + 2], "little", signed=True))
        for index in range(0, len(frames), 2)
    ]
    return max(values) / 32767


def test_pulse_width_changes_square_wave_shape() -> None:
    narrow = [_wave_value(i / 20, "square", pulse_width=0.2) for i in range(20)]
    wide = [_wave_value(i / 20, "square", pulse_width=0.8) for i in range(20)]

    assert sum(value > 0 for value in narrow) < sum(value > 0 for value in wide)


def test_shape_control_changes_saw_wave() -> None:
    clean = [_wave_value(i / 20, "saw", shape=0.0) for i in range(20)]
    shaped = [_wave_value(i / 20, "saw", shape=0.8) for i in range(20)]

    assert clean != shaped


def test_effects_and_output_headroom_render_safely() -> None:
    sample = generate_wave_sample(
        engine="keys",
        waveform="triangle",
        chord="Fm9",
        duration=0.35,
        amplitude=1.0,
        body_level=0.35,
        body_decay=1.2,
        character=0.5,
        metallic=0.25,
        chorus=0.35,
        tremolo_rate=5.5,
        tremolo_depth=0.25,
        output_gain=2.0,
        output_headroom=0.5,
    )

    assert sample.startswith(b"RIFF")
    assert _peak(sample) <= 0.5 + (1 / 32767)
