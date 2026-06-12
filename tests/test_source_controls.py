import io
import wave

from sample_artisan import generate_wave_sample


def _peak(sample: bytes) -> int:
    with wave.open(io.BytesIO(sample), "rb") as wav_file:
        frames = wav_file.readframes(wav_file.getnframes())
    return max(
        abs(int.from_bytes(frames[index : index + 2], "little", signed=True))
        for index in range(0, len(frames), 2)
    )


def test_bass_engine_respects_zero_source_levels() -> None:
    sample = generate_wave_sample(
        engine="bass",
        duration=0.2,
        osc1_level=0,
        osc2_level=0,
        noise_mix=0,
        transient_level=0.8,
        body_level=0.8,
        character=0.6,
    )

    assert _peak(sample) == 0


def test_texture_engine_respects_zero_source_levels() -> None:
    sample = generate_wave_sample(
        engine="texture",
        duration=0.2,
        osc1_level=0,
        osc2_level=0,
        noise_mix=0,
        metallic=1,
        transient_level=0.5,
        body_level=0.5,
        character=0.6,
    )

    assert _peak(sample) == 0


def test_tonal_engine_noise_mix_can_still_generate_noise() -> None:
    sample = generate_wave_sample(
        engine="texture",
        duration=0.2,
        osc1_level=0,
        osc2_level=0,
        noise_mix=1,
        character=0,
    )

    assert _peak(sample) > 0
