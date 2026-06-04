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
    print(f"Audio Sample Generator running at http://{host}:{port}")
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
                frequency=_float_param(params, "frequency", 440.0),
                duration=_float_param(params, "duration", 1.0),
                waveform=params.get("waveform", ["sine"])[0],
                amplitude=_float_param(params, "amplitude", 0.65),
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
            self.send_error(HTTPStatus.BAD_REQUEST, str(error))
            return

        payload = json.dumps(plan.__dict__).encode("utf-8")
        self.send_response(HTTPStatus.OK)
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

    * { box-sizing: border-box; }

    body {
      margin: 0;
      min-height: 100svh;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--ink);
      background: #fff;
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

    label {
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

    select,
    textarea {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #fff;
      color: var(--ink);
      font: inherit;
    }

    select {
      height: 40px;
      padding: 0 10px;
    }

    textarea {
      resize: vertical;
      padding: 10px;
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
      width: 100%;
      min-height: 280px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fbfcfd;
    }

    canvas {
      display: block;
      width: 100%;
      height: 100%;
      min-height: 280px;
    }

    audio { width: 100%; }

    @media (max-width: 780px) {
      main { grid-template-columns: 1fr; }
      aside {
        border-right: 0;
        border-bottom: 1px solid var(--line);
      }
      .workspace { padding: 24px; }
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
      <textarea id="prompt" rows="4" placeholder="short glassy pluck, low gritty bass hit"></textarea>
      <button id="promptButton">Use AI prompt</button>

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
      <input id="duration" type="range" min="0.1" max="3" step="0.1" value="1">

      <label for="amplitude">Amplitude <span class="value" id="amplitudeValue">65%</span></label>
      <input id="amplitude" type="range" min="0.1" max="1" step="0.01" value="0.65">

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
        <canvas id="canvas"></canvas>
      </div>
      <audio id="audio" controls></audio>
    </section>
  </main>

  <script>
    const controls = {
      waveform: document.getElementById("waveform"),
      frequency: document.getElementById("frequency"),
      duration: document.getElementById("duration"),
      amplitude: document.getElementById("amplitude")
    };

    const promptInput = document.getElementById("prompt");
    const promptButton = document.getElementById("promptButton");

    const labels = {
      frequency: document.getElementById("frequencyValue"),
      duration: document.getElementById("durationValue"),
      amplitude: document.getElementById("amplitudeValue")
    };

    const audio = document.getElementById("audio");
    const canvas = document.getElementById("canvas");
    const status = document.getElementById("status");
    const sampleRate = document.getElementById("sampleRate");
    const channels = document.getElementById("channels");
    const context = new AudioContext();
    let currentBuffer = null;

    function updateLabels() {
      labels.frequency.textContent = `${controls.frequency.value} Hz`;
      labels.duration.textContent = `${Number(controls.duration.value).toFixed(1)} s`;
      labels.amplitude.textContent = `${Math.round(Number(controls.amplitude.value) * 100)}%`;
    }

    function buildUrl() {
      const params = new URLSearchParams({
        waveform: controls.waveform.value,
        frequency: controls.frequency.value,
        duration: controls.duration.value,
        amplitude: controls.amplitude.value
      });
      return `/api/sample.wav?${params.toString()}`;
    }

    async function generate() {
      updateLabels();
      status.textContent = "Generating";
      const response = await fetch(buildUrl());
      const bytes = await response.arrayBuffer();
      currentBuffer = await context.decodeAudioData(bytes.slice(0));
      const url = URL.createObjectURL(new Blob([bytes], { type: "audio/wav" }));
      audio.src = url;
      sampleRate.textContent = `${(currentBuffer.sampleRate / 1000).toFixed(1)} kHz`;
      channels.textContent = currentBuffer.numberOfChannels === 1 ? "Mono" : `${currentBuffer.numberOfChannels} channels`;
      status.textContent = `${controls.waveform.value} sample at ${controls.frequency.value} Hz`;
      drawWaveform();
    }

    async function planFromPrompt() {
      const prompt = promptInput.value.trim();
      if (!prompt) {
        status.textContent = "Enter an AI prompt first";
        return;
      }

      status.textContent = "Planning sample with AI";
      try {
        const response = await fetch(`/api/prompt?prompt=${encodeURIComponent(prompt)}`);
        if (!response.ok) {
          throw new Error(await response.text());
        }
        const plan = await response.json();
        controls.waveform.value = plan.waveform;
        controls.frequency.value = Math.round(plan.frequency);
        controls.duration.value = Number(plan.duration).toFixed(1);
        controls.amplitude.value = Number(plan.amplitude).toFixed(2);
        status.textContent = plan.description;
        await generate();
      } catch (error) {
        status.textContent = "AI prompt failed. Try a different prompt.";
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

    Object.values(controls).forEach((control) => {
      control.addEventListener("input", updateLabels);
      control.addEventListener("change", generate);
    });

    document.getElementById("generate").addEventListener("click", generate);
    promptButton.addEventListener("click", planFromPrompt);
    window.addEventListener("resize", drawWaveform);

    updateLabels();
    generate();
  </script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
