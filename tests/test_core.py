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


def test_generate_sample_with_realism_controls() -> None:
    sample = generate_wave_sample(
        engine="percussion",
        frequency=220,
        duration=0.3,
        body_level=0.7,
        body_frequency=180,
        transient_level=0.4,
        character=0.65,
        drift=0.3,
        smear=0.2,
        space=0.18,
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
    assert polished.character >= 0.32
    assert polished.drift >= 0.12
    assert polished.smear >= 0.08
    assert polished.space >= 0.03
    assert sample.startswith(b"RIFF")


def test_cymbal_ai_plan_is_normalized_to_open_hat() -> None:
    plan = _parse_patch(
        '{"engine":"cymbal","waveform":"saw","frequency":1800,'
        '"duration":0.05,"amplitude":0.7,"attack":0.03,"decay":0.04,'
        '"sustain":0.3,"release":0.01,"noise_mix":0.1,'
        '"filter_cutoff":1200,"filter_mode":"lowpass","drive":0.1,'
        '"pitch_drop":0,"metallic":0.1,"bit_depth":16,'
        '"osc2_waveform":"square","osc2_ratio":3,"osc2_level":0.2,'
        '"noise_type":"white","noise_decay":0.08,'
        '"filter_resonance":0.1,"filter_env":0,'
        '"pitch_env":0,"pitch_decay":0.05,'
        '"transient_level":0.1,"transient_tone":6000,'
        '"body_level":0.2,"body_frequency":400,"body_decay":0.2,'
        '"description":"cymbal"}'
    )

    polished = _polish_patch(plan)

    assert polished.engine == "open_hat"
    assert polished.noise_type == "metal"
    assert polished.filter_mode == "highpass"
    assert polished.noise_mix >= 0.55
    assert polished.metallic >= 0.55


def test_ai_plan_falls_back_when_number_fields_are_words() -> None:
    plan = _parse_patch(
        '{"engine":"cymbal","waveform":"saw","frequency":"sine",'
        '"duration":"square","noise_mix":"metal","bit_depth":"triangle",'
        '"description":"cymbal with bad numeric fields"}'
    )

    polished = _polish_patch(plan)

    assert polished.engine == "open_hat"
    assert polished.frequency >= 2500
    assert polished.duration >= 0.18
    assert polished.noise_mix >= 0.55
    assert polished.bit_depth == 16
