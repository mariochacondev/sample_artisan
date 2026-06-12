from sample_artisan.ai import _parse_patch
from sample_artisan.cli import build_parser
from sample_artisan.web import INDEX_HTML


def test_ai_parser_accepts_expanded_synthesis_controls() -> None:
    plan = _parse_patch(
        '{"engine":"keys","waveform":"triangle",'
        '"oscillator_shape":0.3,"pulse_width":0.42,'
        '"chorus":0.25,"tremolo_rate":5,"tremolo_depth":0.4,'
        '"output_gain":1.2,"output_headroom":0.82}'
    )

    assert plan.oscillator_shape == 0.3
    assert plan.pulse_width == 0.42
    assert plan.chorus == 0.25
    assert plan.tremolo_rate == 5
    assert plan.tremolo_depth == 0.4
    assert plan.output_gain == 1.2
    assert plan.output_headroom == 0.82


def test_cli_parser_accepts_expanded_synthesis_controls() -> None:
    args = build_parser().parse_args(
        [
            "rhodes.wav",
            "--engine",
            "keys",
            "--oscillator-shape",
            "0.35",
            "--pulse-width",
            "0.42",
            "--chorus",
            "0.3",
            "--tremolo-rate",
            "5.5",
            "--tremolo-depth",
            "0.25",
            "--output-gain",
            "1.1",
            "--output-headroom",
            "0.84",
        ]
    )

    assert args.oscillator_shape == 0.35
    assert args.pulse_width == 0.42
    assert args.chorus == 0.3
    assert args.tremolo_rate == 5.5
    assert args.tremolo_depth == 0.25
    assert args.output_gain == 1.1
    assert args.output_headroom == 0.84


def test_web_exposes_expanded_controls_and_patch_history() -> None:
    for token in (
        "oscillatorShape",
        "pulseWidth",
        "chorus",
        "tremoloRate",
        "outputGain",
        "outputHeadroom",
        "sample_artisan_patch_history",
        "savePreset",
        "historySelect",
    ):
        assert token in INDEX_HTML
