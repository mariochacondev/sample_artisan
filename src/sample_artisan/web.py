"""Browser interface for generating and viewing sample waveforms."""

from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from sample_artisan.ai import plan_sample_from_prompt
from sample_artisan.synth import generate_wave_sample

HOST = "127.0.0.1"
PORT = 8000


def run(host: str = HOST, port: int = PORT) -> None:
    server = ThreadingHTTPServer((host, port), SampleArtisanHandler)
    print(f"sample_artisan UI running at http://{host}:{port}")
    server.serve_forever()


class SampleArtisanHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        route = urlparse(self.path)
        if route.path == "/":
            self._send_html(INDEX_HTML)
            return
        if route.path == "/api/sample.wav":
            self._send_sample(route.query)
            return
        if route.path == "/api/prompt":
            self._send_prompt_plan(route.query)
            return

        self.send_error(HTTPStatus.NOT_FOUND)

    def log_message(self, format: str, *args: object) -> None:
        return

    def _send_html(self, html: str) -> None:
        encoded = html.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _send_sample(self, query: str) -> None:
        params = parse_qs(query)
        try:
            sample = generate_wave_sample(
                engine=params.get("engine", ["tone"])[0],
                frequency=_float_param(params, "frequency", 440.0),
                duration=_float_param(params, "duration", 1.0),
                waveform=params.get("waveform", ["sine"])[0],
                amplitude=_float_param(params, "amplitude", 0.65),
                attack=_float_param(params, "attack", 0.005),
                decay=_float_param(params, "decay", 0.25),
                sustain=_float_param(params, "sustain", 0.0),
                release=_float_param(params, "release", 0.08),
                noise_mix=_float_param(params, "noise_mix", 0.0),
                filter_cutoff=_float_param(params, "filter_cutoff", 12_000.0),
                filter_mode=params.get("filter_mode", ["lowpass"])[0],
                drive=_float_param(params, "drive", 0.0),
                pitch_drop=_float_param(params, "pitch_drop", 0.0),
                metallic=_float_param(params, "metallic", 0.0),
                bit_depth=int(_float_param(params, "bit_depth", 16)),
                osc2_waveform=params.get("osc2_waveform", ["sine"])[0],
                osc2_ratio=_float_param(params, "osc2_ratio", 1.0),
                osc2_level=_float_param(params, "osc2_level", 0.0),
                noise_type=params.get("noise_type", ["white"])[0],
                noise_decay=_float_param(params, "noise_decay", 0.08),
                filter_resonance=_float_param(params, "filter_resonance", 0.0),
                filter_env=_float_param(params, "filter_env", 0.0),
                pitch_env=_float_param(params, "pitch_env", 0.0),
                pitch_decay=_float_param(params, "pitch_decay", 0.08),
                transient_level=_float_param(params, "transient_level", 0.0),
                transient_tone=_float_param(params, "transient_tone", 1_500.0),
                body_level=_float_param(params, "body_level", 0.0),
                body_frequency=_float_param(params, "body_frequency", 180.0),
                body_decay=_float_param(params, "body_decay", 0.35),
            )
        except ValueError as error:
            self.send_error(HTTPStatus.BAD_REQUEST, str(error))
            return

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "audio/wav")
        self.send_header("Content-Length", str(len(sample)))
        self.end_headers()
        self.wfile.write(sample)

    def _send_prompt_plan(self, query: str) -> None:
        params = parse_qs(query)
        prompt = params.get("prompt", [""])[0]
        try:
            plan = plan_sample_from_prompt(prompt)
        except (RuntimeError, ValueError) as error:
            self._send_json_error(HTTPStatus.BAD_REQUEST, str(error))
            return

        payload = json.dumps(plan.__dict__).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _send_json_error(self, status: HTTPStatus, message: str) -> None:
        payload = json.dumps({"error": message}).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


def _float_param(params: dict[str, list[str]], key: str, default: float) -> float:
    value = params.get(key, [str(default)])[0]
    return float(value)


def main() -> None:
    run()


INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Audio Sample Generator</title>
  <style>
    :root {
      color-scheme: light;
      --ink: #1b1d1f;
      --muted: #62666d;
      --line: #d8dce2;
      --surface: #f7f8fa;
      --accent: #2f7d6d;
      --accent-strong: #225f53;
    }

    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      min-height: 100svh;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--ink);
      background: #ffffff;
    }

    main {
      display: grid;
      grid-template-columns: minmax(260px, 340px) minmax(0, 1fr);
      min-height: 100svh;
    }

    aside {
      padding: 28px;
      border-right: 1px solid var(--line);
      background: var(--surface);
    }

    .workspace {
      display: grid;
      grid-template-rows: auto minmax(280px, 1fr) auto;
      gap: 24px;
      padding: 32px;
      min-width: 0;
    }

    h1 {
      margin: 0 0 8px;
      font-size: 28px;
      line-height: 1.1;
      letter-spacing: 0;
    }

    p {
      margin: 0;
      color: var(--muted);
      line-height: 1.5;
    }

    label,
    legend {
      display: block;
      margin: 22px 0 8px;
      color: #30343a;
      font-size: 13px;
      font-weight: 700;
    }

    input[type="range"] {
      width: 100%;
      accent-color: var(--accent);
    }

    select {
      width: 100%;
      height: 40px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #fff;
      color: var(--ink);
      padding: 0 10px;
      font: inherit;
    }

    textarea {
      width: 100%;
      resize: vertical;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #fff;
      color: var(--ink);
      padding: 10px;
      font: inherit;
      line-height: 1.4;
    }

    button {
      width: 100%;
      height: 44px;
      margin-top: 26px;
      border: 0;
      border-radius: 6px;
      background: var(--accent);
      color: #fff;
      font: inherit;
      font-weight: 800;
      cursor: pointer;
      transition: background 140ms ease, transform 140ms ease;
    }

    button:hover {
      background: var(--accent-strong);
      transform: translateY(-1px);
    }

    button:disabled {
      cursor: wait;
      opacity: 0.72;
      transform: none;
    }

    details {
      margin-top: 24px;
      padding-top: 18px;
      border-top: 1px solid var(--line);
    }

    summary {
      color: #30343a;
      font-size: 13px;
      font-weight: 800;
      cursor: pointer;
    }

    .value {
      float: right;
      color: var(--muted);
      font-weight: 600;
    }

    .topline {
      display: flex;
      justify-content: space-between;
      gap: 16px;
      align-items: end;
    }

    .stats {
      display: flex;
      gap: 16px;
      color: var(--muted);
      font-size: 13px;
      white-space: nowrap;
    }

    .waveform {
      position: relative;
      width: 100%;
      min-height: 280px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fbfcfd;
      overflow: hidden;
    }

    .loader {
      position: absolute;
      inset: 0;
      display: none;
      place-items: center;
      background: rgba(251, 252, 253, 0.78);
      color: var(--accent-strong);
      font-size: 14px;
      font-weight: 800;
      z-index: 2;
    }

    .loader::before {
      content: "";
      width: 24px;
      height: 24px;
      margin-right: 10px;
      border: 3px solid rgba(47, 125, 109, 0.18);
      border-top-color: var(--accent);
      border-radius: 999px;
      animation: spin 800ms linear infinite;
    }

    .is-loading .loader {
      display: flex;
    }

    @keyframes spin {
      to {
        transform: rotate(360deg);
      }
    }

    canvas {
      display: block;
      width: 100%;
      height: 100%;
      min-height: 280px;
    }

    audio {
      width: 100%;
    }

    .patch-details {
      margin: 0;
      max-height: 180px;
      overflow: auto;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #ffffff;
      color: var(--muted);
      padding: 12px;
      font: 12px/1.45 ui-monospace, "SFMono-Regular", Consolas, monospace;
      white-space: pre-wrap;
    }

    @media (max-width: 780px) {
      main {
        grid-template-columns: 1fr;
      }

      aside {
        border-right: 0;
        border-bottom: 1px solid var(--line);
      }

      .workspace {
        padding: 24px;
      }

      .topline {
        align-items: start;
        flex-direction: column;
      }
    }
  </style>
</head>
<body>
  <main>
    <aside>
      <h1>Audio Sample Generator</h1>
      <p>Generate a sample and inspect the waveform from the rendered audio.</p>

      <label for="prompt">AI prompt</label>
      <textarea id="prompt" rows="4" placeholder="closed hi-hat, cymbal, conga, sub kick, gritty bass"></textarea>

      <label for="engine">Sound type</label>
      <select id="engine">
        <option value="tone">Tone</option>
        <option value="kick">Kick</option>
        <option value="snare">Snare</option>
        <option value="closed_hat">Closed hat</option>
        <option value="open_hat">Open hat / cymbal</option>
        <option value="noise">Noise</option>
        <option value="percussion">Percussion</option>
        <option value="bass">Bass</option>
        <option value="pluck">Pluck</option>
        <option value="texture">Texture</option>
      </select>

      <label for="waveform">Waveform</label>
      <select id="waveform">
        <option value="sine">Sine</option>
        <option value="square">Square</option>
        <option value="saw">Saw</option>
        <option value="triangle">Triangle</option>
      </select>

      <label for="frequency">Frequency <span class="value" id="frequencyValue">440 Hz</span></label>
      <input id="frequency" type="range" min="80" max="1200" value="440">

      <label for="duration">Duration <span class="value" id="durationValue">1.0 s</span></label>
      <input id="duration" type="range" min="0.03" max="3" step="0.01" value="1">

      <label for="amplitude">Amplitude <span class="value" id="amplitudeValue">65%</span></label>
      <input id="amplitude" type="range" min="0.1" max="1" step="0.01" value="0.65">

      <label for="attack">Attack <span class="value" id="attackValue">0.005 s</span></label>
      <input id="attack" type="range" min="0" max="0.5" step="0.001" value="0.005">

      <label for="decay">Decay <span class="value" id="decayValue">0.25 s</span></label>
      <input id="decay" type="range" min="0.01" max="2" step="0.01" value="0.25">

      <label for="noiseMix">Noise <span class="value" id="noiseMixValue">0%</span></label>
      <input id="noiseMix" type="range" min="0" max="1" step="0.01" value="0">

      <label for="filterCutoff">Filter <span class="value" id="filterCutoffValue">12000 Hz</span></label>
      <input id="filterCutoff" type="range" min="80" max="18000" step="10" value="12000">

      <label for="filterMode">Filter mode</label>
      <select id="filterMode">
        <option value="lowpass">Lowpass</option>
        <option value="highpass">Highpass</option>
      </select>

      <label for="drive">Drive <span class="value" id="driveValue">0%</span></label>
      <input id="drive" type="range" min="0" max="1" step="0.01" value="0">

      <label for="pitchDrop">Pitch drop <span class="value" id="pitchDropValue">0%</span></label>
      <input id="pitchDrop" type="range" min="0" max="4" step="0.01" value="0">

      <label for="metallic">Metallic <span class="value" id="metallicValue">0%</span></label>
      <input id="metallic" type="range" min="0" max="1" step="0.01" value="0">

      <label for="bitDepth">Bit depth <span class="value" id="bitDepthValue">16 bit</span></label>
      <input id="bitDepth" type="range" min="4" max="16" step="1" value="16">

      <details open>
        <summary>Advanced sound design</summary>

        <label for="osc2Waveform">Oscillator 2 waveform</label>
        <select id="osc2Waveform">
          <option value="sine">Sine</option>
          <option value="square">Square</option>
          <option value="saw">Saw</option>
          <option value="triangle">Triangle</option>
        </select>

        <label for="osc2Ratio">Oscillator 2 ratio <span class="value" id="osc2RatioValue">1.00x</span></label>
        <input id="osc2Ratio" type="range" min="0.25" max="8" step="0.01" value="1">

        <label for="osc2Level">Oscillator 2 level <span class="value" id="osc2LevelValue">0%</span></label>
        <input id="osc2Level" type="range" min="0" max="1" step="0.01" value="0">

        <label for="noiseType">Noise type</label>
        <select id="noiseType">
          <option value="white">White</option>
          <option value="dark">Dark</option>
          <option value="bright">Bright</option>
          <option value="wood">Wood</option>
          <option value="metal">Metal</option>
        </select>

        <label for="noiseDecay">Noise decay <span class="value" id="noiseDecayValue">0.08 s</span></label>
        <input id="noiseDecay" type="range" min="0.005" max="3" step="0.005" value="0.08">

        <label for="filterResonance">Filter resonance <span class="value" id="filterResonanceValue">0%</span></label>
        <input id="filterResonance" type="range" min="0" max="1" step="0.01" value="0">

        <label for="filterEnv">Filter envelope <span class="value" id="filterEnvValue">0%</span></label>
        <input id="filterEnv" type="range" min="-1" max="1" step="0.01" value="0">

        <label for="pitchEnv">Pitch envelope <span class="value" id="pitchEnvValue">0 cents</span></label>
        <input id="pitchEnv" type="range" min="-1200" max="1200" step="1" value="0">

        <label for="pitchDecay">Pitch decay <span class="value" id="pitchDecayValue">0.08 s</span></label>
        <input id="pitchDecay" type="range" min="0.005" max="2" step="0.005" value="0.08">

        <label for="transientLevel">Transient level <span class="value" id="transientLevelValue">0%</span></label>
        <input id="transientLevel" type="range" min="0" max="1" step="0.01" value="0">

        <label for="transientTone">Transient tone <span class="value" id="transientToneValue">1500 Hz</span></label>
        <input id="transientTone" type="range" min="80" max="12000" step="10" value="1500">

        <label for="bodyLevel">Body level <span class="value" id="bodyLevelValue">0%</span></label>
        <input id="bodyLevel" type="range" min="0" max="1" step="0.01" value="0">

        <label for="bodyFrequency">Body frequency <span class="value" id="bodyFrequencyValue">180 Hz</span></label>
        <input id="bodyFrequency" type="range" min="35" max="2000" step="1" value="180">

        <label for="bodyDecay">Body decay <span class="value" id="bodyDecayValue">0.35 s</span></label>
        <input id="bodyDecay" type="range" min="0.02" max="4" step="0.01" value="0.35">
      </details>

      <button id="generate">Generate sample</button>
    </aside>

    <section class="workspace" aria-label="Waveform workspace">
      <div class="topline">
        <div>
          <h1>Waveform</h1>
          <p id="status">Ready</p>
        </div>
        <div class="stats">
          <span id="sampleRate">44.1 kHz</span>
          <span id="channels">Mono</span>
        </div>
      </div>
      <div class="waveform">
        <div class="loader" id="loader">Generating sample</div>
        <canvas id="canvas"></canvas>
      </div>
      <pre class="patch-details" id="patchDetails">Manual patch</pre>
      <audio id="audio" controls></audio>
    </section>
  </main>

  <script>
    const controls = {
      engine: document.getElementById("engine"),
      waveform: document.getElementById("waveform"),
      frequency: document.getElementById("frequency"),
      duration: document.getElementById("duration"),
      amplitude: document.getElementById("amplitude"),
      attack: document.getElementById("attack"),
      decay: document.getElementById("decay"),
      noiseMix: document.getElementById("noiseMix"),
      filterCutoff: document.getElementById("filterCutoff"),
      filterMode: document.getElementById("filterMode"),
      drive: document.getElementById("drive"),
      pitchDrop: document.getElementById("pitchDrop"),
      metallic: document.getElementById("metallic"),
      bitDepth: document.getElementById("bitDepth"),
      osc2Waveform: document.getElementById("osc2Waveform"),
      osc2Ratio: document.getElementById("osc2Ratio"),
      osc2Level: document.getElementById("osc2Level"),
      noiseType: document.getElementById("noiseType"),
      noiseDecay: document.getElementById("noiseDecay"),
      filterResonance: document.getElementById("filterResonance"),
      filterEnv: document.getElementById("filterEnv"),
      pitchEnv: document.getElementById("pitchEnv"),
      pitchDecay: document.getElementById("pitchDecay"),
      transientLevel: document.getElementById("transientLevel"),
      transientTone: document.getElementById("transientTone"),
      bodyLevel: document.getElementById("bodyLevel"),
      bodyFrequency: document.getElementById("bodyFrequency"),
      bodyDecay: document.getElementById("bodyDecay")
    };

    const promptInput = document.getElementById("prompt");
    const generateButton = document.getElementById("generate");

    const labels = {
      frequency: document.getElementById("frequencyValue"),
      duration: document.getElementById("durationValue"),
      amplitude: document.getElementById("amplitudeValue"),
      attack: document.getElementById("attackValue"),
      decay: document.getElementById("decayValue"),
      noiseMix: document.getElementById("noiseMixValue"),
      filterCutoff: document.getElementById("filterCutoffValue"),
      drive: document.getElementById("driveValue"),
      pitchDrop: document.getElementById("pitchDropValue"),
      metallic: document.getElementById("metallicValue"),
      bitDepth: document.getElementById("bitDepthValue"),
      osc2Ratio: document.getElementById("osc2RatioValue"),
      osc2Level: document.getElementById("osc2LevelValue"),
      noiseDecay: document.getElementById("noiseDecayValue"),
      filterResonance: document.getElementById("filterResonanceValue"),
      filterEnv: document.getElementById("filterEnvValue"),
      pitchEnv: document.getElementById("pitchEnvValue"),
      pitchDecay: document.getElementById("pitchDecayValue"),
      transientLevel: document.getElementById("transientLevelValue"),
      transientTone: document.getElementById("transientToneValue"),
      bodyLevel: document.getElementById("bodyLevelValue"),
      bodyFrequency: document.getElementById("bodyFrequencyValue"),
      bodyDecay: document.getElementById("bodyDecayValue")
    };

    const audio = document.getElementById("audio");
    const canvas = document.getElementById("canvas");
    const waveformPanel = document.querySelector(".waveform");
    const loader = document.getElementById("loader");
    const patchDetails = document.getElementById("patchDetails");
    const status = document.getElementById("status");
    const sampleRate = document.getElementById("sampleRate");
    const channels = document.getElementById("channels");
    const context = new AudioContext();
    let currentBuffer = null;
    let activePlan = null;

    function updateLabels() {
      labels.frequency.textContent = `${controls.frequency.value} Hz`;
      labels.duration.textContent = `${Number(controls.duration.value).toFixed(2)} s`;
      labels.amplitude.textContent = `${Math.round(Number(controls.amplitude.value) * 100)}%`;
      labels.attack.textContent = `${Number(controls.attack.value).toFixed(3)} s`;
      labels.decay.textContent = `${Number(controls.decay.value).toFixed(2)} s`;
      labels.noiseMix.textContent = `${Math.round(Number(controls.noiseMix.value) * 100)}%`;
      labels.filterCutoff.textContent = `${controls.filterCutoff.value} Hz`;
      labels.drive.textContent = `${Math.round(Number(controls.drive.value) * 100)}%`;
      labels.pitchDrop.textContent = `${Math.round(Number(controls.pitchDrop.value) * 100)}%`;
      labels.metallic.textContent = `${Math.round(Number(controls.metallic.value) * 100)}%`;
      labels.bitDepth.textContent = `${controls.bitDepth.value} bit`;
      labels.osc2Ratio.textContent = `${Number(controls.osc2Ratio.value).toFixed(2)}x`;
      labels.osc2Level.textContent = `${Math.round(Number(controls.osc2Level.value) * 100)}%`;
      labels.noiseDecay.textContent = `${Number(controls.noiseDecay.value).toFixed(3)} s`;
      labels.filterResonance.textContent = `${Math.round(Number(controls.filterResonance.value) * 100)}%`;
      labels.filterEnv.textContent = `${Math.round(Number(controls.filterEnv.value) * 100)}%`;
      labels.pitchEnv.textContent = `${controls.pitchEnv.value} cents`;
      labels.pitchDecay.textContent = `${Number(controls.pitchDecay.value).toFixed(3)} s`;
      labels.transientLevel.textContent = `${Math.round(Number(controls.transientLevel.value) * 100)}%`;
      labels.transientTone.textContent = `${controls.transientTone.value} Hz`;
      labels.bodyLevel.textContent = `${Math.round(Number(controls.bodyLevel.value) * 100)}%`;
      labels.bodyFrequency.textContent = `${controls.bodyFrequency.value} Hz`;
      labels.bodyDecay.textContent = `${Number(controls.bodyDecay.value).toFixed(2)} s`;
    }

    function buildUrl() {
      const params = new URLSearchParams({
        engine: controls.engine.value,
        waveform: controls.waveform.value,
        frequency: controls.frequency.value,
        duration: controls.duration.value,
        amplitude: controls.amplitude.value,
        attack: controls.attack.value,
        decay: controls.decay.value,
        sustain: 0,
        release: 0.08,
        noise_mix: controls.noiseMix.value,
        filter_cutoff: controls.filterCutoff.value,
        filter_mode: controls.filterMode.value,
        drive: controls.drive.value,
        pitch_drop: controls.pitchDrop.value,
        metallic: controls.metallic.value,
        bit_depth: controls.bitDepth.value,
        osc2_waveform: controls.osc2Waveform.value,
        osc2_ratio: controls.osc2Ratio.value,
        osc2_level: controls.osc2Level.value,
        noise_type: controls.noiseType.value,
        noise_decay: controls.noiseDecay.value,
        filter_resonance: controls.filterResonance.value,
        filter_env: controls.filterEnv.value,
        pitch_env: controls.pitchEnv.value,
        pitch_decay: controls.pitchDecay.value,
        transient_level: controls.transientLevel.value,
        transient_tone: controls.transientTone.value,
        body_level: controls.bodyLevel.value,
        body_frequency: controls.bodyFrequency.value,
        body_decay: controls.bodyDecay.value
      });
      return `/api/sample.wav?${params.toString()}`;
    }
