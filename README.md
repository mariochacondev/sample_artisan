# sample_artisan

`sample_artisan` is an audio sample generator and sound-design tool. It can write WAV samples from the command line and includes a browser interface for shaping a sample while viewing its waveform.

The prompt workflow uses a local Ollama text model as a patch designer. Ollama chooses synth parameters, then `sample_artisan` renders the sound locally with a two-oscillator stack, real chord symbols, noise colors, pitch movement, transients, resonant body, drive, bit depth, and filter shaping.

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

You can also ask Ollama to choose a full synth patch from a prompt:

```bash
sample-artisan sample.wav --prompt "short low gritty bass hit"
sample-artisan chord.wav --prompt "wide detuned Am9 pluck"
```

## Run the waveform interface

```bash
sample-artisan-ui
```

Then open:

```text
http://127.0.0.1:8000
```

The interface generates a WAV sample and draws the waveform from the decoded audio. You can change engine, waveform, frequency, duration, amplitude, envelope, noise, filter, drive, pitch drop, metallic tone, and bit depth, then play the result in the browser.

The dashboard also includes a Chord field and true two-oscillator controls. Osc 1 supports level, octave, semitone, and fine tune. Osc 2 supports waveform, ratio, level, octave, semitone, and fine tune. Chord symbols such as `Am9`, `Cmaj7`, `Dm11`, and `G13` render as real chord tones. No LFO is included yet.

## Ollama prompt mode

The prompt box uses Ollama at `http://127.0.0.1:11434`. Prompt mode requires Ollama to be running; if Ollama is unavailable, manual parameter generation still works.

Supported broad engines are `tone`, `kick`, `snare`, `closed_hat`, `open_hat`, `noise`, `percussion`, `bass`, `pluck`, and `texture`. The AI prompt can still use normal instrument language like "conga", "bongo", "sub kick", or "kalimba"; Ollama maps that language onto the broader patch engine and detailed synth parameters.

Install Ollama, pull a model, then start the interface:

```bash
ollama pull llama3.2
sample-artisan-ui
```

You can choose another Ollama model with:

```bash
export OLLAMA_MODEL="qwen2.5"
```

## Test

```bash
pytest
```
