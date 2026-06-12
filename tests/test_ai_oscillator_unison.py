from sample_artisan.ai import _parse_patch


def test_parse_ai_plan_includes_oscillator_unison_and_detune() -> None:
    plan = _parse_patch(
        '{"engine":"pluck","waveform":"saw",'
        '"oscillator_unison":5,"oscillator_detune":14}'
    )

    assert plan.oscillator_unison == 5
    assert plan.oscillator_detune == 14
