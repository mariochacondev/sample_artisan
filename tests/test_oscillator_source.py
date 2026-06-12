from sample_artisan.synth import OscillatorSpec, SynthPatch, _mix_oscillators, _oscillator_specs


def test_oscillator_specs_capture_patch_tuning_and_levels() -> None:
    specs = _oscillator_specs(
        SynthPatch(
            waveform="saw",
            osc1_level=0.7,
            osc1_octave=1,
            osc2_waveform="triangle",
            osc2_ratio=2,
            osc2_level=0.3,
            osc2_semitone=12,
        ),
        110,
    )

    assert specs[0].waveform == "saw"
    assert round(specs[0].frequency) == 220
    assert specs[0].level == 0.7
    assert specs[1].waveform == "triangle"
    assert round(specs[1].frequency) == 440
    assert specs[1].level == 0.3


def test_oscillator_specs_expand_unison_voices() -> None:
    specs = _oscillator_specs(
        SynthPatch(
            waveform="saw",
            osc1_level=0.9,
            osc2_level=0,
            oscillator_unison=3,
            oscillator_detune=12,
        ),
        220,
    )

    active = [spec for spec in specs if spec.level > 0]

    assert len(active) == 3
    assert round(sum(spec.level for spec in active), 6) == 0.9
    assert active[0].frequency < 220
    assert active[1].frequency == 220
    assert active[2].frequency > 220


def test_oscillator_unison_defaults_to_current_two_voice_source() -> None:
    specs = _oscillator_specs(SynthPatch(osc1_level=1, osc2_level=0), 440)

    assert len(specs) == 2
    assert specs[0].frequency == 440
    assert specs[0].level == 1
    assert specs[1].level == 0


def test_mix_oscillators_returns_silence_for_zero_levels() -> None:
    assert _mix_oscillators(
        (
            OscillatorSpec("saw", 440, 0),
            OscillatorSpec("square", 880, 0),
        ),
        0.01,
    ) == 0


def test_mix_oscillators_uses_weighted_levels() -> None:
    mixed = _mix_oscillators(
        (
            OscillatorSpec("square", 100, 1),
            OscillatorSpec("square", 100, 0),
        ),
        0.001,
    )

    assert mixed == 1.0
