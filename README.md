# Benchmark Atlas

A self-contained common-facts benchmark suite with an interactive dashboard and documented JSON API.

## Run

```powershell
py -m pip install -r requirements.txt
py -m uvicorn server:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000`. The dashboard displays live health data and includes an API-ready control. API documentation is at `/docs`.

## Windows executable

The distributable is `dist/BenchmarkAtlas.exe`. Double-click it to start the local product (it opens the dashboard automatically), or run `BenchmarkAtlas.exe --port 8080` from a terminal.

## API

- `GET /api/health` — service state and uptime
- `GET /api/benchmarks` — full benchmark library (optional `?category=Science`)
- `GET /api/benchmarks/{id}` — an individual benchmark
- `POST /api/benchmarks/{id}/score` — score a comma-separated submission: `{"answer":"Mercury, Venus, ..."}`

## Ollama model client

Benchmark Atlas defaults to Ollama at `http://127.0.0.1:11434/api/chat`. Open **Client settings** to automatically discover installed Ollama models, choose one, and save. Settings persist in `%APPDATA%/BenchmarkAtlas/settings.json`. OpenAI-compatible servers are also supported by entering their full chat-completions endpoint.

## Benchmark repository format

The `benchmarks/` folder is repository-ready: each category has its own directory and a JSONL file with 50 entries. `benchmarks/manifest.json` is the discovery index. The library currently includes History, Science, Geography, Civics, Mathematics, Computing, and Literature (350 questions total). Newer manifest entries may include a `references` array of authoritative sources used to verify the pack.

Each JSONL row uses the stable `benchmark-atlas-jsonl/v1` contract:

```json
{"id":"mathematics-001","title":"Mathematics question 1","category":"Mathematics","difficulty":"Core","prompt":"What is 12 multiplied by 12?","answer":["144"]}
```

Run `python tools/build_packs.py` to regenerate the bundled packs and manifest. The generator asserts exactly 50 records per pack.

To have the client pull packs from GitHub instead of its bundled copy, set `BENCHMARK_REPOSITORY_URL` to the repository's raw-content root, then run the app. For example:

```powershell
$env:BENCHMARK_REPOSITORY_URL = "https://raw.githubusercontent.com/OWNER/benchmark-atlas-data/main/benchmarks"
.\dist\BenchmarkAtlas.exe
```
