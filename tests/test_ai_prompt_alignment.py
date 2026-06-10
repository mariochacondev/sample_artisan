from sample_artisan.ai import _align_patch_to_prompt, _parse_patch, _polish_patch


def test_clap_prompt_overrides_bad_tone_patch() -> None:
    patch = _parse_patch(
        '{"engine":"tone","waveform":"sine","frequency":440,'
        '"duration":1,"amplitude":0.5,"attack":0,"decay":100,'
        '"sustain":0.5,"release":200,"noise_mix":0,'
        '"filter_cutoff":200,"filter_mode":"lowpass","drive":0.2,'
        '"pitch_drop":0,"metallic":1,"bit_depth":16,'
        '"description":"","chord":"","osc1_level":0.5,'
        '"osc1_octave":4,"osc1_semitone":0,"osc1_fine":0,'
        '"osc2_waveform":"sine","osc2_ratio":1,"osc2_level":0.25,'
        '"osc2_octave":5,"osc2_semitone":0,"osc2_fine":0,'
        '"noise_type":"white","noise_decay":100,'
        '"filter_resonance":0.7,"filter_env":0,"pitch_env":0,'
        '"pitch_decay":200,"transient_level":0.5,'
        '"transient_tone":0,"body_level":0.2,'
        '"body_frequency":220,"body_decay":100,'
        '"character":0,"drift":0,"smear":1,"space":1}'
    )

    aligned = _align_patch_to_prompt("clap", patch)
    polished = _polish_patch(aligned)

    assert aligned.engine == "snare"
    assert aligned.chord == ""
    assert polished.engine == "snare"
    assert polished.waveform == "square"
    assert polished.duration <= 0.55
    assert polished.decay <= 0.32
    assert polished.release <= 0.12
    assert polished.noise_mix >= 0.55
    assert polished.filter_mode == "highpass"
    assert polished.transient_level >= 0.25


def test_chord_prompt_preserves_chord_workflow() -> None:
    patch = _parse_patch(
        '{"engine":"tone","waveform":"saw","frequency":440,'
        '"duration":1,"chord":"","description":"wide pluck"}'
    )

    aligned = _align_patch_to_prompt("wide detuned Am9 pluck", patch)

    assert aligned.engine == "pluck"
    assert aligned.chord == "Am9"
