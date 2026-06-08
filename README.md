# sample_artisan

`sample_artisan` is an audio sample generator and sound-design tool. It can write WAV samples from the command line and includes a browser interface for shaping a sample while viewing its waveform.

The prompt workflow uses a local Ollama text model as a patch designer. Ollama chooses synth parameters, then `sample_artisan` renders the sound locally with a two-oscillator stack, real chord symbols, noise colors, pitch movement, transients, resonant body, drive, bit depth, and filter shaping.

## Generate a sample from the command line

```bash
sample-artisan sample.wav --waveform sine --frequency 440 --duration 1.5
sample-artisan chord.wav --engine pluck --waveform saw --chord Am9
```

## Run the waveform interface

```bash
sample-artisan-ui
```

Then open:

```text
http://127.0.0.1:8000
```

The interface can generate real chord symbols such as `Am9`, `Cmaj7`, `Dm11`, and `G13`, and includes Osc 1/Osc 2 controls for waveform, level, octave, semitone, and fine tuning. Osc 2 also supports ratio tuning. No LFO is included yet.

## Ollama prompt setup

The AI prompt path intentionally uses Ollama only. Make sure Ollama is running and the model exists before using the prompt field:

```bash
ollama serve
ollama pull llama3.2
```

If the app can reach Ollama but the first prompt is slow while the model loads, increase the request timeout:

```bash
OLLAMA_TIMEOUT=180 sample-artisan-ui
```

Useful Ollama settings:

- `OLLAMA_URL`: defaults to `http://127.0.0.1:11434/api/generate`
- `OLLAMA_MODEL`: defaults to `llama3.2`
- `OLLAMA_TIMEOUT`: defaults to `120`
- `OLLAMA_NUM_PREDICT`: defaults to `700`
- `OLLAMA_KEEP_ALIVE`: defaults to `10m`

## Test

```bash
pytest
```
