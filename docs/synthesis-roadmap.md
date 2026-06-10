# Synthesis depth roadmap

`sample_artisan` should keep Ollama as the patch designer, but the synth needs a deeper sound engine so the model can design richer and more believable samples. This roadmap captures the direction for moving from simple named engines toward a modular synth/sampler-style instrument.

## Core principle

Ollama should decide what sound to design and how to set the patch. Python should provide expressive audio building blocks, validation, rendering, and safe output gain. Avoid prompt-specific hardcoded rules in Python; add capability and context instead.

## Why this matters

A model can only design inside the instrument it controls. If the renderer exposes only basic waveform, envelope, filter, and noise controls, Ollama can make useful simple one-shots but will struggle with sounds like upright piano, Rhodes, Juno pads, Korg-style plucks, realistic percussion, or polished FX.

The goal is to give the AI a Serum/Vital-like parameter surface: enough modules, modulation, tone shaping, and effects that good prompts can become good patches.

## Target architecture

### 1. Patch schema

Create a richer structured patch model that can describe modules independently instead of placing every parameter directly on `SynthPatch`.

Suggested sections:

- `source`: oscillator, sample, wavetable, noise, or hybrid source selection.
- `oscillators`: waveform, level, tuning, phase, unison, detune, width, blend.
- `exciter`: hammer, pick, bow, click, breath, stick, or noise burst.
- `resonator`: string, tine, body, plate, tube, membrane, or modal bank.
- `filter`: type, cutoff, resonance, drive, key tracking, envelope amount.
- `amp`: attack, decay, sustain, release, curve, velocity response.
- `modulation`: envelopes and LFOs routed to pitch, filter, level, wavetable position, pan, or effects.
- `effects`: saturation, chorus, tremolo, delay, reverb, cabinet, EQ, compression/limiting.
- `output`: headroom, width, normalization, fade, final gain.
- `description`: short human-readable explanation from Ollama.

### 2. Sound modules

Build modules that can be combined by engines rather than making every engine a separate closed system.

Initial module priorities:

- Oscillator stack with phase control, shape blending, unison, detune, and stereo width.
- Noise/exciter layer with envelope, tone, color, and transient shaping.
- Modal resonator bank for piano strings, Rhodes tines, bells, mallets, plates, and percussion bodies.
- Filter models with lowpass, highpass, bandpass, resonance, drive, and envelope tracking.
- Effects chain with chorus, tremolo, saturation, room, delay, and simple EQ.
- Output limiter/headroom stage that prevents accidental clipping without overriding the creative patch.

### 3. Instrument families

Keep engines as helpful families, but make them presets over shared modules rather than isolated behavior.

Suggested families:

- `drum`: kick, snare, clap, hats, cymbals, percussion.
- `keys`: upright piano, electric piano, Rhodes, Wurlitzer, toy piano.
- `synth`: subtractive, wavetable-like, supersaw, bass, pluck, lead, pad.
- `mallet`: marimba, vibraphone, kalimba, bell, glass.
- `texture`: ambience, riser, impact, noise bed, transition FX.
- `sample_layer`: future support for loading or generating sample-based layers.

### 4. Ollama context

The Ollama prompt should describe available modules and give sound-design examples by family. The context should teach the model how to use the synth, not patch around weak renderer behavior.

Examples to include over time:

- Upright piano: soft hammer, string partials, soundboard body, low drive, moderate room, controlled headroom.
- Rhodes: tine resonator, bell partial, pickup/body, tremolo, chorus, soft saturation.
- Juno pad: saw/square blend, chorus, slow filter envelope, LFO drift, wide stereo.
- Korg-style pluck: bright oscillator, fast attack, short decay, resonant lowpass, delay/space.
- Clap: layered noise bursts, highpass, short transient spacing, no chord.
- 808/kick: sine body, pitch envelope, transient click, controlled saturation.

### 5. UI direction

The UI should reflect the modular structure without becoming cluttered.

Recommended layout:

- Keep the prompt and main generation controls visible first.
- Add grouped sections for Source, Amp, Filter, Motion, Body/Resonance, Effects, and Output.
- Hide advanced modulation routing until needed.
- Show the final JSON patch clearly so users can understand and tweak what Ollama produced.
- Keep the waveform/sample viewer after the controls and compact enough to fit the screen.

## Milestones

### Milestone 1: stabilize current engine

- Make every visible control affect the engines where it appears relevant.
- Add regression tests for silent states, waveform changes, chord rendering, and output headroom.
- Keep Ollama context aligned with the exact capabilities exposed in the renderer.

### Milestone 2: modular patch internals

- Introduce internal module functions for oscillators, exciters, resonators, filters, effects, and output.
- Keep backward compatibility with the current flat `SynthPatch` while adding cleaner internals.
- Add typed data structures for future nested patch sections.

### Milestone 3: better keys and electric piano

- Replace the current simple keys approximation with a modal/resonator-based keys engine.
- Add Rhodes/Wurlitzer-oriented controls: tine, bell, pickup, tremolo, chorus, cabinet, key-off noise.
- Add focused Ollama examples for piano, Rhodes, and soft harmonic chords.

### Milestone 4: synth depth

- Add unison, detune, phase/random, oscillator blend, pulse width, and wavetable-like shape morphing.
- Add envelopes/LFOs with a small modulation matrix.
- Add Juno-style chorus and better saturation.

### Milestone 5: sample quality and export polish

- Add fades, anti-click protection, oversampling or safer nonlinear stages where needed.
- Add simple loudness/peak analysis in generated patch metadata.
- Add preset saving/loading and prompt history.

## Testing approach

Each new audio module should have tests for:

- WAV generation succeeds.
- Silent or zero-level states are actually silent.
- Key controls produce measurably different output.
- Invalid patch values fail clearly or normalize safely.
- Dense patches stay under output headroom.

Do not rely only on waveform byte differences for sound quality. Add targeted signal checks when possible, such as peak level, RMS range, zero crossings, envelope decay, or frequency-domain energy bands.
