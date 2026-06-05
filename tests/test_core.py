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


def test_percussion_ai_plan_uses_resonant_body() -> None:
    plan = _parse_patch(
        '{"engine":"percussion","waveform":"triangle","frequency":900,'
        '"duration":0.05,"amplitude":0.75,"attack":0.03,"decay":0.03,'
        '"sustain":0.5,"release":0.01,"noise_mix":0,'
        '"filter_cutoff":12000,"filter_mode":"highpass","drive":0.2,'
        '"pitch_drop":2,"metallic":0.8,"bit_depth":16,'
        '"osc2_waveform":"sine","osc2_ratio":1.5,"osc2_level":0.2,'
        '"noise_type":"metal","noise_decay":0.04,'
        '"filter_resonance":0.4,"filter_env":0,'
        '"pitch_env":0,"pitch_decay":0.05,'
        '"transient_level":0,"transient_tone":1800,'
        '"body_level":0,"body_frequency":900,"body_decay":0.04,'
        '"description":"conga"}'
    )

    polished = _polish_patch(plan)
    sample = generate_wave_sample(
        engine=polished.engine,
        waveform=polished.waveform,
        frequency=polished.frequency,
        duration=polished.duration,
        amplitude=polished.amplitude,
        attack=polished.attack,
        decay=polished.decay,
        noise_mix=polished.noise_mix,
        filter_cutoff=polished.filter_cutoff,
        filter_mode=polished.filter_mode,
        pitch_drop=polished.pitch_drop,
        transient_level=polished.transient_level,
        body_level=polished.body_level,
        body_frequency=polished.body_frequency,
        body_decay=polished.body_decay,
    )

    assert polished.engine == "percussion"
    assert polished.body_level >= 0.35
    assert 120 <= polished.body_frequency <= 520
    assert polished.transient_level >= 0.12
    assert sample.startswith(b"RIFF")
