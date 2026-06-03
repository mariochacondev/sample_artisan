"""Command-line interface for sample_artisan."""

from __future__ import annotations

import argparse

from sample_artisan.core import craft_sample


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sample-artisan")
    parser.add_argument("text", help="Text to craft into a sample message.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    print(craft_sample(args.text))


if __name__ == "__main__":
    main()
