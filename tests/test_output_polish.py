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


def test_rendered_sample_has_zeroed_edges() -> None:
    frames = _pcm_frames(
        generate_wave_sample(
            engine="tone",
            waveform="saw",
            frequency=440,
            duration=0.2,
            attack=0,
            decay=0.2,
            sustain=1,
            release=0,
            amplitude=1,
        )
    )

    assert frames[0] == 0
    assert frames[-1] == 0
    assert max(abs(frame) for frame in frames[200:-200]) > 0


def test_output_headroom_still_applies_after_edge_fades() -> None:
    frames = _pcm_frames(
        generate_wave_sample(
            engine="texture",
            waveform="saw",
            chord="Fm9",
            duration=0.4,
            amplitude=1,
            noise_mix=0.4,
            metallic=1,
            drive=1,
            filter_resonance=1,
            space=1,
            character=1,
        )
    )

    assert max(abs(frame) for frame in frames) <= int(32767 * 0.92) + 1
