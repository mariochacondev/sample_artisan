import pytest

from sample_artisan import generate_wave_sample
from sample_artisan.cli import build_parser


def test_generate_wave_sample_returns_wav_bytes() -> None:
    sample = generate_wave_sample(frequency=440, duration=0.1, waveform="sine")

    assert sample.startswith(b"RIFF")
    assert b"WAVE" in sample[:16]
    assert len(sample) > 1000


def test_generate_wave_sample_rejects_unknown_waveform() -> None:
    with pytest.raises(ValueError, match="unsupported waveform"):
        generate_wave_sample(waveform="noise")


def test_cli_parser_defaults_to_sample_wav() -> None:
    args = build_parser().parse_args([])

    assert args.output == "sample.wav"
    assert args.waveform == "sine"
    assert args.frequency == 440.0
