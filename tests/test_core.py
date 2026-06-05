import pytest

from sample_artisan import generate_wave_sample
from sample_artisan.ai import _parse_patch, _polish_patch
from sample_artisan.cli import build_parser


def test_generate_wave_sample_returns_wav_bytes() -> None:
    sample = generate_wave_sample(frequency=440, duration=0.1, waveform="sine")

    assert sample.startswith(b"RIFF")
    assert b"WAVE" in sample[:16]
    assert len(sample) > 1000


def test_generate_wave_sample_rejects_unknown_waveform() -> None:
    with pytest.raises(ValueError, match="unsupported waveform"):
        generate_wave_sample(waveform="noise")


def test_generate_closed_hat_uses_advanced_engine() -> None:
    sample = generate_wave_sample(
        engine="closed_hat",
        frequency=7500,
        duration=0.08,
        noise_mix=0.95,
        filter_mode="highpass",
        filter_cutoff=7000,
        metallic=0.9,
    )

    assert sample.startswith(b"RIFF")
    assert len(sample) > 1000


def test_cli_parser_defaults_to_sample_wav() -> None:
    args = build_parser().parse_args([])

    assert args.output == "sample.wav"
    assert args.engine == "tone"
    assert args.waveform == "sine"
    assert args.frequency == 440.0


def test_parse_ai_sample_plan() -> None:
    plan = _parse_patch(
        '{"engine":"closed_hat","waveform":"square","frequency":7500,'
        '"duration":0.08,"amplitude":0.8,"attack":0.001,"decay":0.05,'
        '"sustain":0,"release":0.01,"noise_mix":0.95,'
        '"filter_cutoff":7000,"filter_mode":"highpass","drive":0.2,'
        '"pitch_drop":0,"metallic":0.9,"bit_depth":12,'
        '"description":"tight hat"}'
    )

    assert plan.engine == "closed_hat"
    assert plan.frequency == 7500
    assert plan.filter_mode == "highpass"
    assert plan.amplitude == 0.8


def test_kick_ai_plan_is_polished_into_sub_range() -> None:
    plan = _parse_patch(
        '{"engine":"kick","waveform":"square","frequency":236,'
        '"duration":0.08,"amplitude":0.8,"attack":0.02,"decay":0.05,'
        '"sustain":0.4,"release":0.01,"noise_mix":0.8,'
        '"filter_cutoff":7000,"filter_mode":"highpass","drive":0.2,'
        '"pitch_drop":0,"metallic":0.9,"bit_depth":12,'
        '"description":"sub kick"}'
    )

    polished = _polish_patch(plan)

    assert polished.engine == "kick"
    assert polished.waveform == "sine"
    assert polished.frequency <= 90
    assert polished.duration >= 0.18
    assert polished.decay >= 0.12
    assert polished.filter_mode == "lowpass"
    assert polished.filter_cutoff <= 1800
    assert polished.pitch_drop >= 1.6
    assert polished.metallic == 0.0
