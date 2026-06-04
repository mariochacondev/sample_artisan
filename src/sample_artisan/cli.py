"""Command-line interface for generating audio samples."""

from __future__ import annotations

import argparse
from pathlib import Path

from sample_artisan.ai import plan_sample_from_prompt
from sample_artisan import generate_wave_sample
from sample_artisan.synth import render_patch


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
        choices=["sine", "square", "saw", "triangle"],
        default="sine",
        help="Waveform shape to generate.",
    )
    parser.add_argument(
        "--engine",
        choices=["tone", "kick", "snare", "closed_hat", "open_hat", "noise"],
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
    )
    output_path = Path(args.output)
    output_path.write_bytes(sample)
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
