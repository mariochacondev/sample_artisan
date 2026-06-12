import io
import wave

from sample_artisan import generate_wave_sample
from sample_artisan.cli import build_parser


def test_cli_parser_accepts_oscillator_controls() -> None:
    args = build_parser().parse_args(
        [
            "pluck.wav",
            "--engine",
            "pluck",
            "--waveform",
            "saw",
            "--chord",
            "Am9",
            "--osc1-level",
            "0.8",
            "--osc1-octave",
            "0",
            "--osc1-semitone",
            "0",
            "--osc1-fine",
            "3",
            "--osc2-waveform",
            "triangle",
            "--osc2-ratio",
            "1.5",
            "--osc2-level",
            "0.35",
            "--osc2-octave",
            "1",
            "--osc2-semitone",
            "7",
            "--osc2-fine",
            "-5",
            "--oscillator-unison",
            "4",
            "--oscillator-detune",
            "12",
        ]
    )

    assert args.output == "pluck.wav"
    assert args.engine == "pluck"
    assert args.waveform == "saw"
    assert args.chord == "Am9"
    assert args.osc1_level == 0.8
    assert args.osc1_fine == 3
    assert args.osc2_waveform == "triangle"
    assert args.osc2_ratio == 1.5
    assert args.osc2_level == 0.35
    assert args.osc2_octave == 1
    assert args.osc2_semitone == 7
    assert args.osc2_fine == -5
    assert args.oscillator_unison == 4
    assert args.oscillator_detune == 12


def test_cli_exposed_oscillator_controls_render_audio() -> None:
    args = build_parser().parse_args(
        [
            "pluck.wav",
            "--engine",
            "pluck",
            "--waveform",
            "saw",
            "--chord",
            "Am9",
            "--duration",
            "0.25",
            "--osc2-waveform",
            "triangle",
            "--osc2-level",
            "0.4",
            "--oscillator-unison",
            "3",
            "--oscillator-detune",
            "8",
        ]
    )

    sample = generate_wave_sample(
        engine=args.engine,
        waveform=args.waveform,
        frequency=args.frequency,
        duration=args.duration,
        amplitude=args.amplitude,
        chord=args.chord,
        osc1_level=args.osc1_level,
        osc1_octave=args.osc1_octave,
        osc1_semitone=args.osc1_semitone,
        osc1_fine=args.osc1_fine,
        osc2_waveform=args.osc2_waveform,
        osc2_ratio=args.osc2_ratio,
        osc2_level=args.osc2_level,
        osc2_octave=args.osc2_octave,
        osc2_semitone=args.osc2_semitone,
        osc2_fine=args.osc2_fine,
        oscillator_unison=args.oscillator_unison,
        oscillator_detune=args.oscillator_detune,
    )

    with wave.open(io.BytesIO(sample), "rb") as wav_file:
        assert wav_file.getnframes() > 1000
        assert wav_file.getnchannels() == 1
