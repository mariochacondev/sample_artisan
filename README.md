# sample_artisan

`sample_artisan` is an audio sample generator and sound-design tool. It can write WAV samples from the command line and includes a browser interface for shaping a sample while viewing its waveform.

The prompt workflow uses a local Ollama text model as a patch designer. Ollama chooses synth parameters, then `sample_artisan` renders the sound locally with a two-oscillator stack, real chord symbols, noise colors, pitch movement, transients, resonant body, oscillator shaping, chorus, tremolo, drive, bit depth, filter shaping, and output headroom.

## Generate a sample from the command line

```bash
sample-artisan sample.wav --waveform sine --frequency 440 --duration 1.5
sample-artisan chord.wav --engine pluck --waveform saw --chord Am9
sample-artisan wide-pluck.wav --engine pluck --waveform saw --chord Am9 --osc2-waveform triangle --osc2-level 0.35 --oscillator-unison 4 --oscillator-detune 12
sample-artisan rhodes.wav --engine keys --waveform triangle --chord Fm9 --chorus 0.35 --tremolo-rate 5.5 --tremolo-depth 0.25 --output-headroom 0.84
```

The command line supports the same core oscillator controls as the browser: chord symbols, Osc 1/Osc 2 levels, octave/semitone/fine tuning, Osc 2 ratio, unison voice count, unison detune, oscillator shape, pulse width, chorus, tremolo, output gain, and output headroom.

## Run the waveform interface

```bash
sample-artisan-ui
```

Then open:

```text
http://127.0.0.1:8000
```

The interface can generate real chord symbols such as `Am9`, `Cmaj7`, `Dm11`, and `G13`, and includes Osc 1/Osc 2 controls for waveform, level, octave, semitone, fine tuning, unison, detune, shape, and pulse width. Advanced controls include body/resonance, chorus, tremolo, space, and output headroom. The browser also keeps a local patch history so generated or manually saved patches can be reloaded while comparing sounds.

## Synthesis roadmap

The project is moving toward a deeper modular synth/sampler-style engine so Ollama can do better sound design instead of choosing from shallow preset-like engines. See [`docs/synthesis-roadmap.md`](docs/synthesis-roadmap.md) for the planned patch architecture, module priorities, instrument families, UI direction, and testing approach.

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
- `OLLAMA_NUM_PREDICT`: defaults to `900`
- `OLLAMA_KEEP_ALIVE`: defaults to `10m`

## Test

```bash
pytest
```
