import io
import wave

from sample_artisan import generate_wave_sample


def _pcm_frames(sample: bytes) -> list[int]:
    with wave.open(io.BytesIO(sample), "rb") as wav_file:
        frames = wav_file.readframes(wav_file.getnframes())
    return [
        int.from_bytes(frames[index : index + 2], "little", signed=True)
        for index in range(0, len(frames), 2)
    ]


def test_keys_engine_is_silent_when_oscillators_and_noise_are_down() -> None:
    sample = generate_wave_sample(
        engine="keys",
        chord="Fm9",
        duration=0.25,
        osc1_level=0,
        osc2_level=0,
        noise_mix=0,
        transient_level=0.8,
        body_level=0.8,
        character=0.5,
    )

    assert max(abs(frame) for frame in _pcm_frames(sample)) == 0


def test_keys_engine_waveform_changes_rendered_sample() -> None:
    sine = generate_wave_sample(
        engine="keys",
        chord="Fm9",
        duration=0.25,
        waveform="sine",
        osc1_level=1,
        osc2_level=0,
        noise_mix=0,
        transient_level=0,
        body_level=0,
        character=0.2,
    )
    saw = generate_wave_sample(
        engine="keys",
        chord="Fm9",
        duration=0.25,
        waveform="saw",
        osc1_level=1,
        osc2_level=0,
        noise_mix=0,
        transient_level=0,
        body_level=0,
        character=0.2,
    )

    assert sine != saw
