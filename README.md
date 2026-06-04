# sample_artisan

`sample_artisan` is an audio sample generator. It can write WAV samples from the command line and includes a browser interface for shaping a sample while viewing its waveform.

## Project layout

```text
sample_artisan/
├── pyproject.toml
├── README.md
├── src/
│   └── sample_artisan/
│       ├── __init__.py
│       ├── ai.py
│       ├── cli.py
│       ├── core.py
│       ├── synth.py
│       └── web.py
└── tests/
    └── test_core.py
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## Generate a sample from the command line

```bash
sample-artisan sample.wav --waveform sine --frequency 440 --duration 1.5
```

You can also ask AI to choose the parameters:

```bash
export OPENAI_API_KEY="your-api-key"
sample-artisan sample.wav --prompt "short low gritty bass hit"
```

## Run the waveform interface

```bash
sample-artisan-ui
```

Then open:

```text
http://127.0.0.1:8000
```

The interface generates a WAV sample and draws the waveform from the decoded audio. You can change waveform, frequency, duration, and amplitude, then play the result in the browser.

To use the AI prompt box, set `OPENAI_API_KEY` before starting the interface:

```bash
export OPENAI_API_KEY="your-api-key"
sample-artisan-ui
```

## Test

```bash
pytest
```
