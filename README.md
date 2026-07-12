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

## Benchmark repository format

The `benchmarks/` folder is repository-ready: each category has its own directory and a JSONL file with 50 entries. `benchmarks/manifest.json` is the discovery index.

To have the client pull packs from GitHub instead of its bundled copy, set `BENCHMARK_REPOSITORY_URL` to the repository's raw-content root, then run the app. For example:

```powershell
$env:BENCHMARK_REPOSITORY_URL = "https://raw.githubusercontent.com/OWNER/benchmark-atlas-data/main/benchmarks"
.\dist\BenchmarkAtlas.exe
```
