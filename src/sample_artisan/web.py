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
        payload = html.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _send_sample(self, query: str) -> None:
        params = parse_qs(query)
        try:
            sample = generate_wave_sample(
                engine=_text_param(params, "engine", "tone"),
                waveform=_text_param(params, "waveform", "sine"),
                frequency=_float_param(params, "frequency", 440.0),
                duration=_float_param(params, "duration", 1.0),
                amplitude=_float_param(params, "amplitude", 0.65),
                attack=_float_param(params, "attack", 0.005),
                decay=_float_param(params, "decay", 0.25),
                sustain=_float_param(params, "sustain", 0.0),
                release=_float_param(params, "release", 0.08),
                noise_mix=_float_param(params, "noise_mix", 0.0),
                filter_cutoff=_float_param(params, "filter_cutoff", 12_000.0),
                filter_mode=_text_param(params, "filter_mode", "lowpass"),
                drive=_float_param(params, "drive", 0.0),
                pitch_drop=_float_param(params, "pitch_drop", 0.0),
                metallic=_float_param(params, "metallic", 0.0),
                bit_depth=int(_float_param(params, "bit_depth", 16)),
                osc2_waveform=_text_param(params, "osc2_waveform", "sine"),
                osc2_ratio=_float_param(params, "osc2_ratio", 1.0),
                osc2_level=_float_param(params, "osc2_level", 0.0),
                noise_type=_text_param(params, "noise_type", "white"),
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
            self._send_json_error(HTTPStatus.BAD_REQUEST, str(error))
            return

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "audio/wav")
        self.send_header("Content-Length", str(len(sample)))
        self.end_headers()
        self.wfile.write(sample)

    def _send_prompt_plan(self, query: str) -> None:
        prompt = parse_qs(query).get("prompt", [""])[0]
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


def _text_param(params: dict[str, list[str]], key: str, default: str) -> str:
    return params.get(key, [default])[0]


def _float_param(params: dict[str, list[str]], key: str, default: float) -> float:
    return float(params.get(key, [str(default)])[0])


def main() -> None:
    run()


INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>sample_artisan</title>
  <style>
    :root { --ink:#1b1d1f; --muted:#62666d; --line:#d8dce2; --surface:#f7f8fa; --accent:#2f7d6d; --accent-strong:#225f53; }
    * { box-sizing:border-box; }
    body { margin:0; min-height:100svh; font-family:Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color:var(--ink); background:#fff; }
    main { display:grid; grid-template-columns:minmax(280px, 360px) minmax(0, 1fr); min-height:100svh; }
    aside { padding:28px; border-right:1px solid var(--line); background:var(--surface); overflow:auto; }
    .workspace { display:grid; grid-template-rows:auto minmax(280px, 1fr) auto auto; gap:20px; padding:32px; min-width:0; }
    h1 { margin:0 0 8px; font-size:28px; line-height:1.1; letter-spacing:0; }
    p { margin:0; color:var(--muted); line-height:1.5; }
    label { display:block; margin:18px 0 8px; color:#30343a; font-size:13px; font-weight:700; }
    input[type="range"], select, textarea, button { width:100%; font:inherit; }
    input[type="range"] { accent-color:var(--accent); }
    select, textarea { border:1px solid var(--line); border-radius:6px; background:#fff; color:var(--ink); padding:9px 10px; }
    button { height:44px; margin-top:24px; border:0; border-radius:6px; background:var(--accent); color:#fff; font-weight:800; cursor:pointer; }
    button:hover { background:var(--accent-strong); }
    button:disabled { cursor:wait; opacity:.72; }
    details { margin-top:22px; padding-top:16px; border-top:1px solid var(--line); }
    summary { color:#30343a; font-size:13px; font-weight:800; cursor:pointer; }
    .value { float:right; color:var(--muted); font-weight:600; }
    .topline { display:flex; justify-content:space-between; gap:16px; align-items:end; }
    .stats { display:flex; gap:16px; color:var(--muted); font-size:13px; white-space:nowrap; }
    .waveform { position:relative; width:100%; min-height:280px; border:1px solid var(--line); border-radius:8px; background:#fbfcfd; overflow:hidden; }
    canvas { display:block; width:100%; height:100%; min-height:280px; }
    audio { width:100%; }
    .loader { position:absolute; inset:0; display:none; place-items:center; background:rgba(251,252,253,.78); color:var(--accent-strong); font-size:14px; font-weight:800; z-index:2; }
    .loader::before { content:""; width:24px; height:24px; margin-right:10px; border:3px solid rgba(47,125,109,.18); border-top-color:var(--accent); border-radius:999px; animation:spin 800ms linear infinite; }
    .is-loading .loader { display:flex; }
    .patch-details { margin:0; max-height:180px; overflow:auto; border:1px solid var(--line); border-radius:6px; background:#fff; color:var(--muted); padding:12px; font:12px/1.45 ui-monospace, "SFMono-Regular", Consolas, monospace; white-space:pre-wrap; }
    @keyframes spin { to { transform:rotate(360deg); } }
    @media (max-width:780px) { main { grid-template-columns:1fr; } aside { border-right:0; border-bottom:1px solid var(--line); } .workspace { padding:24px; } .topline { align-items:start; flex-direction:column; } }
  </style>
</head>
<body>
  <main>
    <aside>
      <h1>Audio Sample Generator</h1>
      <p>Generate a sample and inspect the rendered waveform.</p>

      <label for="prompt">AI prompt</label>
      <textarea id="prompt" rows="4" placeholder="closed hi-hat, cymbal, conga, sub kick, gritty bass"></textarea>

      <label for="engine">Sound type</label>
      <select id="engine">
        <option value="tone">Tone</option><option value="kick">Kick</option><option value="snare">Snare</option>
        <option value="closed_hat">Closed hat</option><option value="open_hat">Open hat / cymbal</option>
        <option value="noise">Noise</option><option value="percussion">Percussion</option>
        <option value="bass">Bass</option><option value="pluck">Pluck</option><option value="texture">Texture</option>
      </select>

      <label for="waveform">Waveform</label>
      <select id="waveform"><option value="sine">Sine</option><option value="square">Square</option><option value="saw">Saw</option><option value="triangle">Triangle</option></select>

      <label for="frequency">Frequency <span class="value" id="frequencyValue"></span></label><input id="frequency" type="range" min="80" max="1200" value="440">
      <label for="duration">Duration <span class="value" id="durationValue"></span></label><input id="duration" type="range" min="0.03" max="3" step="0.01" value="1">
      <label for="amplitude">Amplitude <span class="value" id="amplitudeValue"></span></label><input id="amplitude" type="range" min="0.1" max="1" step="0.01" value="0.65">
      <label for="attack">Attack <span class="value" id="attackValue"></span></label><input id="attack" type="range" min="0" max="0.5" step="0.001" value="0.005">
      <label for="decay">Decay <span class="value" id="decayValue"></span></label><input id="decay" type="range" min="0.01" max="2" step="0.01" value="0.25">
      <label for="noiseMix">Noise <span class="value" id="noiseMixValue"></span></label><input id="noiseMix" type="range" min="0" max="1" step="0.01" value="0">
      <label for="filterCutoff">Filter <span class="value" id="filterCutoffValue"></span></label><input id="filterCutoff" type="range" min="80" max="18000" step="10" value="12000">
      <label for="filterMode">Filter mode</label><select id="filterMode"><option value="lowpass">Lowpass</option><option value="highpass">Highpass</option></select>
      <label for="drive">Drive <span class="value" id="driveValue"></span></label><input id="drive" type="range" min="0" max="1" step="0.01" value="0">
      <label for="pitchDrop">Pitch drop <span class="value" id="pitchDropValue"></span></label><input id="pitchDrop" type="range" min="0" max="4" step="0.01" value="0">
      <label for="metallic">Metallic <span class="value" id="metallicValue"></span></label><input id="metallic" type="range" min="0" max="1" step="0.01" value="0">
      <label for="bitDepth">Bit depth <span class="value" id="bitDepthValue"></span></label><input id="bitDepth" type="range" min="4" max="16" step="1" value="16">

      <details open>
        <summary>Advanced sound design</summary>
        <label for="osc2Waveform">Oscillator 2 waveform</label><select id="osc2Waveform"><option value="sine">Sine</option><option value="square">Square</option><option value="saw">Saw</option><option value="triangle">Triangle</option></select>
        <label for="osc2Ratio">Oscillator 2 ratio <span class="value" id="osc2RatioValue"></span></label><input id="osc2Ratio" type="range" min="0.25" max="8" step="0.01" value="1">
        <label for="osc2Level">Oscillator 2 level <span class="value" id="osc2LevelValue"></span></label><input id="osc2Level" type="range" min="0" max="1" step="0.01" value="0">
        <label for="noiseType">Noise type</label><select id="noiseType"><option value="white">White</option><option value="dark">Dark</option><option value="bright">Bright</option><option value="wood">Wood</option><option value="metal">Metal</option></select>
        <label for="noiseDecay">Noise decay <span class="value" id="noiseDecayValue"></span></label><input id="noiseDecay" type="range" min="0.005" max="3" step="0.005" value="0.08">
        <label for="filterResonance">Filter resonance <span class="value" id="filterResonanceValue"></span></label><input id="filterResonance" type="range" min="0" max="1" step="0.01" value="0">
        <label for="filterEnv">Filter envelope <span class="value" id="filterEnvValue"></span></label><input id="filterEnv" type="range" min="-1" max="1" step="0.01" value="0">
        <label for="pitchEnv">Pitch envelope <span class="value" id="pitchEnvValue"></span></label><input id="pitchEnv" type="range" min="-1200" max="1200" step="1" value="0">
        <label for="pitchDecay">Pitch decay <span class="value" id="pitchDecayValue"></span></label><input id="pitchDecay" type="range" min="0.005" max="2" step="0.005" value="0.08">
        <label for="transientLevel">Transient level <span class="value" id="transientLevelValue"></span></label><input id="transientLevel" type="range" min="0" max="1" step="0.01" value="0">
        <label for="transientTone">Transient tone <span class="value" id="transientToneValue"></span></label><input id="transientTone" type="range" min="80" max="12000" step="10" value="1500">
        <label for="bodyLevel">Body level <span class="value" id="bodyLevelValue"></span></label><input id="bodyLevel" type="range" min="0" max="1" step="0.01" value="0">
        <label for="bodyFrequency">Body frequency <span class="value" id="bodyFrequencyValue"></span></label><input id="bodyFrequency" type="range" min="35" max="2000" step="1" value="180">
        <label for="bodyDecay">Body decay <span class="value" id="bodyDecayValue"></span></label><input id="bodyDecay" type="range" min="0.02" max="4" step="0.01" value="0.35">
      </details>

      <button id="generate">Generate sample</button>
    </aside>

    <section class="workspace" aria-label="Waveform workspace">
      <div class="topline"><div><h1>Waveform</h1><p id="status">Ready</p></div><div class="stats"><span id="sampleRate">44.1 kHz</span><span id="channels">Mono</span></div></div>
      <div class="waveform"><div class="loader" id="loader">Generating sample</div><canvas id="canvas"></canvas></div>
      <pre class="patch-details" id="patchDetails">Manual patch</pre>
      <audio id="audio" controls></audio>
    </section>
  </main>

  <script>
    const ids = ["engine","waveform","frequency","duration","amplitude","attack","decay","noiseMix","filterCutoff","filterMode","drive","pitchDrop","metallic","bitDepth","osc2Waveform","osc2Ratio","osc2Level","noiseType","noiseDecay","filterResonance","filterEnv","pitchEnv","pitchDecay","transientLevel","transientTone","bodyLevel","bodyFrequency","bodyDecay"];
    const controls = Object.fromEntries(ids.map((id) => [id, document.getElementById(id)]));
    const labelIds = ["frequency","duration","amplitude","attack","decay","noiseMix","filterCutoff","drive","pitchDrop","metallic","bitDepth","osc2Ratio","osc2Level","noiseDecay","filterResonance","filterEnv","pitchEnv","pitchDecay","transientLevel","transientTone","bodyLevel","bodyFrequency","bodyDecay"];
    const labels = Object.fromEntries(labelIds.map((id) => [id, document.getElementById(`${id}Value`)]));
    const promptInput = document.getElementById("prompt");
    const generateButton = document.getElementById("generate");
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

    const percent = (value) => `${Math.round(Number(value) * 100)}%`;
    const fixed = (value, digits) => Number(value).toFixed(digits);

    function updateLabels() {
      labels.frequency.textContent = `${controls.frequency.value} Hz`;
      labels.duration.textContent = `${fixed(controls.duration.value, 2)} s`;
      labels.amplitude.textContent = percent(controls.amplitude.value);
      labels.attack.textContent = `${fixed(controls.attack.value, 3)} s`;
      labels.decay.textContent = `${fixed(controls.decay.value, 2)} s`;
      labels.noiseMix.textContent = percent(controls.noiseMix.value);
      labels.filterCutoff.textContent = `${controls.filterCutoff.value} Hz`;
      labels.drive.textContent = percent(controls.drive.value);
      labels.pitchDrop.textContent = percent(controls.pitchDrop.value);
      labels.metallic.textContent = percent(controls.metallic.value);
      labels.bitDepth.textContent = `${controls.bitDepth.value} bit`;
      labels.osc2Ratio.textContent = `${fixed(controls.osc2Ratio.value, 2)}x`;
      labels.osc2Level.textContent = percent(controls.osc2Level.value);
      labels.noiseDecay.textContent = `${fixed(controls.noiseDecay.value, 3)} s`;
      labels.filterResonance.textContent = percent(controls.filterResonance.value);
      labels.filterEnv.textContent = percent(controls.filterEnv.value);
      labels.pitchEnv.textContent = `${controls.pitchEnv.value} cents`;
      labels.pitchDecay.textContent = `${fixed(controls.pitchDecay.value, 3)} s`;
      labels.transientLevel.textContent = percent(controls.transientLevel.value);
      labels.transientTone.textContent = `${controls.transientTone.value} Hz`;
      labels.bodyLevel.textContent = percent(controls.bodyLevel.value);
      labels.bodyFrequency.textContent = `${controls.bodyFrequency.value} Hz`;
      labels.bodyDecay.textContent = `${fixed(controls.bodyDecay.value, 2)} s`;
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

    function setLoading(isLoading, message = "Generating sample") {
      waveformPanel.classList.toggle("is-loading", isLoading);
      generateButton.disabled = isLoading;
      generateButton.textContent = isLoading ? "Generating..." : "Generate sample";
      loader.textContent = message;
    }

    async function renderFromControls(message = "", loadingMessage = "Generating sample") {
      updateLabels();
      status.textContent = "Generating";
      setLoading(true, loadingMessage);
      try {
        const response = await fetch(buildUrl());
        if (!response.ok) throw new Error(await readError(response));
        const bytes = await response.arrayBuffer();
        currentBuffer = await context.decodeAudioData(bytes.slice(0));
        audio.src = URL.createObjectURL(new Blob([bytes], { type: "audio/wav" }));
        sampleRate.textContent = `${(currentBuffer.sampleRate / 1000).toFixed(1)} kHz`;
        channels.textContent = currentBuffer.numberOfChannels === 1 ? "Mono" : `${currentBuffer.numberOfChannels} channels`;
        status.textContent = message || `${controls.engine.value} sample at ${controls.frequency.value} Hz`;
        drawWaveform();
      } catch (error) {
        status.textContent = error.message;
      } finally {
        setLoading(false);
      }
    }

    async function generate() {
      if (generateButton.disabled) return;
      const prompt = promptInput.value.trim();
      if (!prompt) {
        patchDetails.textContent = "Manual patch";
        await renderFromControls();
        return;
      }
      await planFromPrompt(prompt);
    }

    async function planFromPrompt(prompt) {
      status.textContent = "Planning sample with AI";
      setLoading(true, "Planning with AI");
      try {
        const response = await fetch(`/api/prompt?prompt=${encodeURIComponent(prompt)}`);
        if (!response.ok) throw new Error(await readError(response));
        const plan = await response.json();
        applyPlan(plan);
        patchDetails.textContent = JSON.stringify(plan, null, 2);
        await renderFromControls(plan.description, "Generating sample");
      } catch (error) {
        status.textContent = `AI prompt failed: ${error.message}`;
        setLoading(false);
      }
    }

    function applyPlan(plan) {
      const map = {
        engine:"engine", waveform:"waveform", frequency:"frequency", duration:"duration", amplitude:"amplitude", attack:"attack", decay:"decay",
        noise_mix:"noiseMix", filter_cutoff:"filterCutoff", filter_mode:"filterMode", drive:"drive", pitch_drop:"pitchDrop", metallic:"metallic",
        bit_depth:"bitDepth", osc2_waveform:"osc2Waveform", osc2_ratio:"osc2Ratio", osc2_level:"osc2Level", noise_type:"noiseType",
        noise_decay:"noiseDecay", filter_resonance:"filterResonance", filter_env:"filterEnv", pitch_env:"pitchEnv", pitch_decay:"pitchDecay",
        transient_level:"transientLevel", transient_tone:"transientTone", body_level:"bodyLevel", body_frequency:"bodyFrequency", body_decay:"bodyDecay"
      };
      Object.entries(map).forEach(([key, id]) => {
        if (plan[key] !== undefined && controls[id]) controls[id].value = plan[key];
      });
      updateLabels();
    }

    async function readError(response) {
      const text = await response.text();
      try {
        const payload = JSON.parse(text);
        return payload.error || text;
      } catch {
        return text.replace(/<[^>]*>/g, " ").replace(/\\s+/g, " ").trim();
      }
    }

    function drawWaveform() {
      if (!currentBuffer) return;
      const rect = canvas.getBoundingClientRect();
      const scale = window.devicePixelRatio || 1;
      canvas.width = Math.max(1, Math.floor(rect.width * scale));
      canvas.height = Math.max(1, Math.floor(rect.height * scale));
      const ctx = canvas.getContext("2d");
      ctx.scale(scale, scale);
      ctx.clearRect(0, 0, rect.width, rect.height);
      const data = currentBuffer.getChannelData(0);
      const centerY = rect.height / 2;
      const samplesPerPixel = Math.max(1, Math.floor(data.length / rect.width));
      ctx.strokeStyle = "#d8dce2";
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(0, centerY);
      ctx.lineTo(rect.width, centerY);
      ctx.stroke();
      ctx.strokeStyle = "#2f7d6d";
      ctx.lineWidth = 2;
      ctx.beginPath();
      for (let x = 0; x < rect.width; x += 1) {
        const start = x * samplesPerPixel;
        let min = 1;
        let max = -1;
        for (let i = 0; i < samplesPerPixel && start + i < data.length; i += 1) {
          const value = data[start + i];
          min = Math.min(min, value);
          max = Math.max(max, value);
        }
        ctx.moveTo(x, centerY + min * centerY * 0.86);
        ctx.lineTo(x, centerY + max * centerY * 0.86);
      }
      ctx.stroke();
    }

    Object.values(controls).forEach((control) => control.addEventListener("input", updateLabels));
    generateButton.addEventListener("click", generate);
    window.addEventListener("resize", drawWaveform);
    updateLabels();
    generate();
  </script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
