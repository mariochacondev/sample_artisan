from sample_artisan.web import INDEX_HTML


def test_web_controls_include_oscillator_unison_and_detune() -> None:
    assert "oscillatorUnison" in INDEX_HTML
    assert "oscillatorDetune" in INDEX_HTML
    assert "oscillator_unison" in INDEX_HTML
    assert "oscillator_detune" in INDEX_HTML
