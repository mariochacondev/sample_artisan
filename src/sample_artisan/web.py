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
                chord=_text_param(params, "chord", ""),
                osc1_level=_float_param(params, "osc1_level", 1.0),
                osc1_octave=int(_float_param(params, "osc1_octave", 0)),
                osc1_semitone=int(_float_param(params, "osc1_semitone", 0)),
                osc1_fine=_float_param(params, "osc1_fine", 0.0),
                osc2_waveform=_text_param(params, "osc2_waveform", "sine"),
                osc2_ratio=_float_param(params, "osc2_ratio", 1.0),
                osc2_level=_float_param(params, "osc2_level", 0.0),
                osc2_octave=int(_float_param(params, "osc2_octave", 0)),
                osc2_semitone=int(_float_param(params, "osc2_semitone", 0)),
                osc2_fine=_float_param(params, "osc2_fine", 0.0),
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
                character=_float_param(params, "character", 0.0),
                drift=_float_param(params, "drift", 0.0),
                smear=_float_param(params, "smear", 0.0),
                space=_float_param(params, "space", 0.0),
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
    main { display:grid; grid-template-rows:auto minmax(230px, 1fr); min-height:100svh; }
    .parameters { padding:14px 18px; border-bottom:1px solid var(--line); background:var(--surface); }
    .workspace { display:grid; grid-template-rows:auto minmax(110px, 1fr) auto auto; gap:8px; min-height:230px; min-width:0; padding:12px 18px; }
    .panel-head { display:flex; justify-content:space-between; gap:16px; align-items:end; margin-bottom:10px; }
    .panel-head button { width:auto; min-width:180px; margin:0; }
    .control-grid { display:grid; grid-template-columns:repeat(auto-fit, minmax(170px, 1fr)); gap:8px 12px; align-items:end; }
    .prompt-field { grid-column:span 2; }
    h1 { margin:0 0 4px; font-size:24px; line-height:1.1; letter-spacing:0; }
    p { margin:0; color:var(--muted); line-height:1.35; }
    label { display:block; margin:0 0 4px; color:#30343a; font-size:13px; font-weight:700; }
    input, select, textarea, button { width:100%; font:inherit; }
    input[type="range"] { accent-color:var(--accent); }
    input[type="text"], select, textarea { border:1px solid var(--line); border-radius:6px; background:#fff; color:var(--ink); padding:7px 9px; }
    textarea { min-height:68px; }
    button { height:40px; border:0; border-radius:6px; background:var(--accent); color:#fff; font-weight:800; cursor:pointer; }
    button:hover { background:var(--accent-strong); }
    button:disabled { cursor:wait; opacity:.72; }
    details { margin-top:10px; padding-top:10px; border-top:1px solid var(--line); }
    summary { color:#30343a; font-size:13px; font-weight:800; cursor:pointer; }
    .value { float:right; color:var(--muted); font-weight:600; }
    .topline { display:flex; justify-content:space-between; gap:16px; align-items:end; }
    .stats { display:flex; gap:16px; color:var(--muted); font-size:13px; white-space:nowrap; }
    .waveform { position:relative; width:50%; min-height:0; border:1px solid var(--line); border-radius:8px; background:#fbfcfd; overflow:hidden; }
    canvas { display:block; width:100%; height:100%; min-height:0; }
    audio { width:100%; height:32px; }
    .loader { position:absolute; inset:0; display:none; place-items:center; background:rgba(251,252,253,.78); color:var(--accent-strong); font-size:14px; font-weight:800; z-index:2; }
    .is-loading .loader { display:flex; }
    .patch-details { margin:0; max-height:56px; overflow:auto; border:1px solid var(--line); border-radius:6px; background:#fff; color:var(--muted); padding:7px 9px; font:11px/1.35 ui-monospace, "SFMono-Regular", Consolas, monospace; white-space:pre-wrap; }
    @media (max-width:780px) { main { grid-template-rows:auto minmax(220px, 1fr); } .parameters, .workspace { padding:12px; } .workspace { grid-template-rows:auto minmax(92px, 1fr) auto auto; gap:7px; min-height:220px; } .panel-head, .topline { align-items:stretch; flex-direction:column; } .panel-head button { width:100%; } .prompt-field { grid-column:1 / -1; } h1 { font-size:22px; } }
  </style>
</head>
<body>
  <main>
    <section class="parameters" aria-label="Sample parameters">
      <div class="panel-head">
        <div>
          <h1>Audio Sample Generator</h1>
          <p>Prompt a sound or shape the patch manually.</p>
        </div>
        <button id="generate">Generate sample</button>
      </div>
      <div class="control-grid" id="mainControls"></div>
      <details open><summary>Oscillators</summary><div class="control-grid" id="oscControls"></div></details>
      <details><summary>Advanced sound design</summary><div class="control-grid" id="advancedControls"></div></details>
    </section>
    <section class="workspace" aria-label="Waveform workspace">
      <div class="topline"><div><h1>Waveform</h1><p id="status">Ready</p></div><div class="stats"><span id="sampleRate">44.1 kHz</span><span id="channels">Mono</span></div></div>
      <div class="waveform"><div class="loader" id="loader">Generating sample</div><canvas id="canvas"></canvas></div>
      <pre class="patch-details" id="patchDetails">Manual patch</pre>
      <audio id="audio" controls></audio>
    </section>
  </main>
  <script>
    const fieldDefs = [
      ["mainControls","prompt","AI prompt","textarea","wide detuned Am9 pluck, gritty bass, dry conga"],
      ["mainControls","chord","Chord","text","Am9, Cmaj7, Dm11, G13"],
      ["mainControls","engine","Sound type","select",[["tone","Tone"],["kick","Kick"],["snare","Snare"],["closed_hat","Closed hat"],["open_hat","Open hat / cymbal"],["noise","Noise"],["percussion","Percussion"],["bass","Bass"],["pluck","Pluck"],["texture","Texture"]]],
      ["mainControls","waveform","Osc 1 waveform","select",[["sine","Sine"],["square","Square"],["saw","Saw"],["triangle","Triangle"]]],
      ["mainControls","frequency","Frequency","range",[80,1200,1,440,"Hz"]],
      ["mainControls","duration","Duration","range",[0.03,3,0.01,1,"s"]],
      ["mainControls","amplitude","Amplitude","range",[0.1,1,0.01,0.65,"%"]],
      ["mainControls","attack","Attack","range",[0,0.5,0.001,0.005,"s"]],
      ["mainControls","decay","Decay","range",[0.01,2,0.01,0.25,"s"]],
      ["mainControls","noiseMix","Noise","range",[0,1,0.01,0,"%"]],
      ["mainControls","filterCutoff","Filter","range",[80,18000,10,12000,"Hz"]],
      ["mainControls","filterMode","Filter mode","select",[["lowpass","Lowpass"],["highpass","Highpass"]]],
      ["mainControls","drive","Drive","range",[0,1,0.01,0,"%"]],
      ["mainControls","pitchDrop","Pitch drop","range",[0,4,0.01,0,"%"]],
      ["mainControls","metallic","Metallic","range",[0,1,0.01,0,"%"]],
      ["mainControls","bitDepth","Bit depth","range",[4,16,1,16,"bit"]],
      ["oscControls","osc1Level","Osc 1 level","range",[0,1,0.01,1,"%"]],
      ["oscControls","osc1Octave","Osc 1 octave","range",[-4,4,1,0,""]],
      ["oscControls","osc1Semitone","Osc 1 semitone","range",[-24,24,1,0,"st"]],
      ["oscControls","osc1Fine","Osc 1 fine","range",[-100,100,1,0,"cents"]],
      ["oscControls","osc2Waveform","Osc 2 waveform","select",[["sine","Sine"],["square","Square"],["saw","Saw"],["triangle","Triangle"]]],
      ["oscControls","osc2Ratio","Osc 2 ratio","range",[0.25,8,0.01,1,"x"]],
      ["oscControls","osc2Level","Osc 2 level","range",[0,1,0.01,0,"%"]],
      ["oscControls","osc2Octave","Osc 2 octave","range",[-4,4,1,0,""]],
      ["oscControls","osc2Semitone","Osc 2 semitone","range",[-24,24,1,0,"st"]],
      ["oscControls","osc2Fine","Osc 2 fine","range",[-100,100,1,0,"cents"]],
      ["advancedControls","noiseType","Noise type","select",[["white","White"],["dark","Dark"],["bright","Bright"],["wood","Wood"],["metal","Metal"]]],
      ["advancedControls","noiseDecay","Noise decay","range",[0.005,3,0.005,0.08,"s"]],
      ["advancedControls","filterResonance","Filter resonance","range",[0,1,0.01,0,"%"]],
      ["advancedControls","filterEnv","Filter envelope","range",[-1,1,0.01,0,"%"]],
      ["advancedControls","pitchEnv","Pitch envelope","range",[-1200,1200,1,0,"cents"]],
      ["advancedControls","pitchDecay","Pitch decay","range",[0.005,2,0.005,0.08,"s"]],
      ["advancedControls","transientLevel","Transient level","range",[0,1,0.01,0,"%"]],
      ["advancedControls","transientTone","Transient tone","range",[80,12000,10,1500,"Hz"]],
      ["advancedControls","bodyLevel","Body level","range",[0,1,0.01,0,"%"]],
      ["advancedControls","bodyFrequency","Body frequency","range",[35,2000,1,180,"Hz"]],
      ["advancedControls","bodyDecay","Body decay","range",[0.02,4,0.01,0.35,"s"]],
      ["advancedControls","character","Character","range",[0,1,0.01,0,"%"]],
      ["advancedControls","drift","Drift","range",[0,1,0.01,0,"%"]],
      ["advancedControls","smear","Smear","range",[0,1,0.01,0,"%"]],
      ["advancedControls","space","Space","range",[0,1,0.01,0,"%"]]
    ];
    const labels = {};
    const controls = {};

    function addField([section,id,label,type,config]) {
      const field = document.createElement("div");
      field.className = id === "prompt" ? "field prompt-field" : "field";
      const labelEl = document.createElement("label");
      labelEl.htmlFor = id;
      labelEl.textContent = label;
      if (type === "range") {
        const value = document.createElement("span");
        value.className = "value";
        value.id = `${id}Value`;
        labelEl.append(" ", value);
        labels[id] = value;
      }
      field.append(labelEl);
      let input;
      if (type === "select") {
        input = document.createElement("select");
        config.forEach(([value, text]) => input.add(new Option(text, value)));
      } else if (type === "textarea") {
        input = document.createElement("textarea");
        input.rows = 3;
        input.placeholder = config;
      } else {
        input = document.createElement("input");
        input.type = type;
        if (type === "range") {
          [input.min, input.max, input.step, input.value] = config;
        } else {
          input.placeholder = config;
        }
      }
      input.id = id;
      field.append(input);
      document.getElementById(section).append(field);
      controls[id] = input;
    }
    fieldDefs.forEach(addField);

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

    function formatValue(id, value) {
      const def = fieldDefs.find((item) => item[1] === id);
      const unit = def && def[3] === "range" ? def[4][4] : "";
      if (unit === "%") return `${Math.round(Number(value) * 100)}%`;
      if (unit === "s") return `${Number(value).toFixed(3)} s`;
      return `${value}${unit ? ` ${unit}` : ""}`;
    }
    function updateLabels() {
      Object.entries(labels).forEach(([id, label]) => label.textContent = formatValue(id, controls[id].value));
    }
    function buildUrl() {
      const params = new URLSearchParams({
        engine: controls.engine.value, waveform: controls.waveform.value, frequency: controls.frequency.value,
        duration: controls.duration.value, amplitude: controls.amplitude.value, attack: controls.attack.value,
        decay: controls.decay.value, sustain: 0, release: 0.08, noise_mix: controls.noiseMix.value,
        filter_cutoff: controls.filterCutoff.value, filter_mode: controls.filterMode.value, drive: controls.drive.value,
        pitch_drop: controls.pitchDrop.value, metallic: controls.metallic.value, bit_depth: controls.bitDepth.value,
        chord: controls.chord.value, osc1_level: controls.osc1Level.value, osc1_octave: controls.osc1Octave.value,
        osc1_semitone: controls.osc1Semitone.value, osc1_fine: controls.osc1Fine.value, osc2_waveform: controls.osc2Waveform.value,
        osc2_ratio: controls.osc2Ratio.value, osc2_level: controls.osc2Level.value, osc2_octave: controls.osc2Octave.value,
        osc2_semitone: controls.osc2Semitone.value, osc2_fine: controls.osc2Fine.value, noise_type: controls.noiseType.value,
        noise_decay: controls.noiseDecay.value, filter_resonance: controls.filterResonance.value, filter_env: controls.filterEnv.value,
        pitch_env: controls.pitchEnv.value, pitch_decay: controls.pitchDecay.value, transient_level: controls.transientLevel.value,
        transient_tone: controls.transientTone.value, body_level: controls.bodyLevel.value, body_frequency: controls.bodyFrequency.value,
        body_decay: controls.bodyDecay.value, character: controls.character.value, drift: controls.drift.value,
        smear: controls.smear.value, space: controls.space.value
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
        status.textContent = message || `${controls.engine.value} ${controls.chord.value.trim() || "sample"}`;
        drawWaveform();
      } catch (error) {
        status.textContent = error.message;
      } finally {
        setLoading(false);
      }
    }
    async function generate() {
      if (generateButton.disabled) return;
      const prompt = controls.prompt.value.trim();
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
        engine:"engine", waveform:"waveform", frequency:"frequency", duration:"duration", amplitude:"amplitude",
        attack:"attack", decay:"decay", noise_mix:"noiseMix", filter_cutoff:"filterCutoff", filter_mode:"filterMode",
        drive:"drive", pitch_drop:"pitchDrop", metallic:"metallic", bit_depth:"bitDepth", chord:"chord",
        osc1_level:"osc1Level", osc1_octave:"osc1Octave", osc1_semitone:"osc1Semitone", osc1_fine:"osc1Fine",
        osc2_waveform:"osc2Waveform", osc2_ratio:"osc2Ratio", osc2_level:"osc2Level", osc2_octave:"osc2Octave",
        osc2_semitone:"osc2Semitone", osc2_fine:"osc2Fine", noise_type:"noiseType", noise_decay:"noiseDecay",
        filter_resonance:"filterResonance", filter_env:"filterEnv", pitch_env:"pitchEnv", pitch_decay:"pitchDecay",
        transient_level:"transientLevel", transient_tone:"transientTone", body_level:"bodyLevel",
        body_frequency:"bodyFrequency", body_decay:"bodyDecay", character:"character", drift:"drift",
        smear:"smear", space:"space"
      };
      Object.entries(map).forEach(([key, id]) => {
        if (plan[key] !== undefined && controls[id]) controls[id].value = plan[key];
      });
      updateLabels();
    }
    async function readError(response) {
      const text = await response.text();
      try { return JSON.parse(text).error || text; }
      catch { return text.replace(/<[^>]*>/g, " ").replace(/\s+/g, " ").trim(); }
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
      ctx.beginPath();
      ctx.moveTo(0, centerY);
      ctx.lineTo(rect.width, centerY);
      ctx.stroke();
      ctx.strokeStyle = "#2f7d6d";
      ctx.lineWidth = 2;
      ctx.beginPath();
      for (let x = 0; x < rect.width; x += 1) {
        const start = x * samplesPerPixel;
        let min = 1, max = -1;
        for (let i = 0; i < samplesPerPixel && start + i < data.length; i += 1) {
          min = Math.min(min, data[start + i]);
          max = Math.max(max, data[start + i]);
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
