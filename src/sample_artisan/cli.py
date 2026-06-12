"""Command-line interface for generating audio samples."""

from __future__ import annotations

import argparse
from pathlib import Path

from sample_artisan.ai import plan_sample_from_prompt
from sample_artisan import generate_wave_sample
from sample_artisan.synth import ENGINES, WAVEFORMS, render_patch


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sample-artisan")
    parser.add_argument(
        "output",
        nargs="?",
        default="sample.wav",
        help="Path for the generated WAV sample.",
    )
    parser.add_argument(
        "--prompt",
        help="Use AI to turn a sound-design prompt into sample parameters.",
    )
    parser.add_argument(
        "--waveform",
        choices=list(WAVEFORMS),
        default="sine",
        help="Oscillator 1 waveform shape.",
    )
    parser.add_argument(
        "--engine",
        choices=list(ENGINES),
        default="tone",
        help="Synthesis engine to use.",
    )
    parser.add_argument(
        "--frequency",
        type=float,
        default=440.0,
        help="Fundamental frequency in Hz.",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=1.0,
        help="Sample duration in seconds.",
    )
    parser.add_argument(
        "--amplitude",
        type=float,
        default=0.65,
        help="Amplitude between 0 and 1.",
    )
    parser.add_argument(
        "--chord",
        default="",
        help="Optional chord symbol such as Am9, Cmaj7, or Fm9.",
    )
    parser.add_argument(
        "--osc1-level",
        type=float,
        default=1.0,
        help="Oscillator 1 level between 0 and 1.",
    )
    parser.add_argument(
        "--osc1-octave",
        type=int,
        default=0,
        help="Oscillator 1 octave offset.",
    )
    parser.add_argument(
        "--osc1-semitone",
        type=int,
        default=0,
        help="Oscillator 1 semitone offset.",
    )
    parser.add_argument(
        "--osc1-fine",
        type=float,
        default=0.0,
        help="Oscillator 1 fine tuning in cents.",
    )
    parser.add_argument(
        "--osc2-waveform",
        choices=list(WAVEFORMS),
        default="sine",
        help="Oscillator 2 waveform shape.",
    )
    parser.add_argument(
        "--osc2-ratio",
        type=float,
        default=1.0,
        help="Oscillator 2 frequency ratio.",
    )
    parser.add_argument(
        "--osc2-level",
        type=float,
        default=0.0,
        help="Oscillator 2 level between 0 and 1.",
    )
    parser.add_argument(
        "--osc2-octave",
        type=int,
        default=0,
        help="Oscillator 2 octave offset.",
    )
    parser.add_argument(
        "--osc2-semitone",
        type=int,
        default=0,
        help="Oscillator 2 semitone offset.",
    )
    parser.add_argument(
        "--osc2-fine",
        type=float,
        default=0.0,
        help="Oscillator 2 fine tuning in cents.",
    )
    parser.add_argument(
        "--oscillator-unison",
        type=int,
        default=1,
        help="Number of unison voices per oscillator, from 1 to 8.",
    )
    parser.add_argument(
        "--oscillator-detune",
        type=float,
        default=0.0,
        help="Unison detune amount in cents.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.prompt:
        plan = plan_sample_from_prompt(args.prompt)
        sample = render_patch(plan)
        output_path = Path(args.output)
        output_path.write_bytes(sample)
        print(plan.description)
        print(f"Wrote {output_path}")
        return

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
    output_path = Path(args.output)
    output_path.write_bytes(sample)
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
