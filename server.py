"""Benchmark Atlas — self-contained API and web UI."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
import time
import sys
import webbrowser
import os
from urllib.request import urlopen
from urllib.request import Request

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# PyInstaller unpacks bundled assets into _MEIPASS; source runs use this folder.
ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
DATA_FILE = ROOT / "data" / "benchmarks.json"
PACKS_DIR = ROOT / "benchmarks"
REPOSITORY_URL = os.getenv("BENCHMARK_REPOSITORY_URL", "").rstrip("/")
MODEL_ENDPOINT = os.getenv("MODEL_ENDPOINT_URL", "").rstrip("/")
started = time.time()
api_enabled = True

app = FastAPI(title="Benchmark Atlas API", version="1.0.0", description="A practical common-facts benchmark API.")
app.mount("/assets", StaticFiles(directory=ROOT / "web"), name="assets")


def load_benchmarks():
    if REPOSITORY_URL:
        manifest = json.loads(urlopen(f"{REPOSITORY_URL}/manifest.json", timeout=10).read())
        return [json.loads(line) for pack in manifest["packs"]
                for line in urlopen(f"{REPOSITORY_URL}/{pack['path']}", timeout=10).read().decode().splitlines() if line.strip()]
    if PACKS_DIR.exists():
        return [json.loads(line) for path in PACKS_DIR.glob("*/*.jsonl")
                for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))


class Answer(BaseModel):
    answer: str


class ClientConfig(BaseModel):
    atlas_url: str = ""
    model_endpoint: str = ""


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(ROOT / "web" / "index.html")


@app.get("/api/health")
def health():
    return {"status": "online" if api_enabled else "paused", "version": app.version,
            "uptime_seconds": round(time.time() - started), "timestamp": datetime.now(timezone.utc).isoformat()}


@app.get("/api/source")
def source():
    return {"mode": "github" if REPOSITORY_URL else "bundled", "repository": REPOSITORY_URL or None,
            "format": "category JSONL"}


@app.get("/api/config")
def config():
    return {"atlas_url": REPOSITORY_URL, "model_endpoint": MODEL_ENDPOINT}


@app.post("/api/config")
def update_config(config: ClientConfig):
    global REPOSITORY_URL, MODEL_ENDPOINT
    REPOSITORY_URL = config.atlas_url.rstrip("/")
    MODEL_ENDPOINT = config.model_endpoint.rstrip("/")
    # Validate the Atlas source immediately, so a bad URL is never silently saved.
    if REPOSITORY_URL:
        try:
            load_benchmarks()
        except Exception as exc:
            REPOSITORY_URL = ""
            raise HTTPException(400, f"Could not load Atlas manifest: {exc}")
    return {"atlas_url": REPOSITORY_URL, "model_endpoint": MODEL_ENDPOINT}


@app.post("/api/benchmarks/{benchmark_id}/run-model")
def run_model(benchmark_id: str):
    if not MODEL_ENDPOINT:
        raise HTTPException(400, "Set a model endpoint in Client settings first.")
    item = next((x for x in load_benchmarks() if x["id"] == benchmark_id), None)
    if not item:
        raise HTTPException(404, "Benchmark not found")
    payload = {"model": "benchmark-client", "messages": [
        {"role": "system", "content": "Answer only with a comma-separated answer. Do not explain."},
        {"role": "user", "content": item["prompt"]}], "temperature": 0}
    try:
        request = Request(MODEL_ENDPOINT, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"}, method="POST")
        response = json.loads(urlopen(request, timeout=45).read())
        answer = response["choices"][0]["message"]["content"].strip()
    except Exception as exc:
        raise HTTPException(502, f"Model endpoint failed: {exc}")
    return {"answer": answer, "benchmark_id": benchmark_id}


@app.post("/api/control/start")
def start_api():
    global api_enabled
    api_enabled = True
    return {"status": "online", "message": "API is ready to accept benchmark requests."}


@app.get("/api/benchmarks")
def benchmarks(category: str | None = None):
    items = load_benchmarks()
    if category:
        items = [item for item in items if item["category"].lower() == category.lower()]
    return {"count": len(items), "items": items}


@app.get("/api/benchmarks/{benchmark_id}")
def benchmark(benchmark_id: str):
    for item in load_benchmarks():
        if item["id"] == benchmark_id:
            return item
    raise HTTPException(404, "Benchmark not found")


@app.post("/api/benchmarks/{benchmark_id}/score")
def score(benchmark_id: str, submission: Answer):
    for item in load_benchmarks():
        if item["id"] == benchmark_id:
            expected = [x.strip().casefold() for x in item["answer"]]
            provided = [x.strip().casefold() for x in submission.answer.replace(";", ",").split(",") if x.strip()]
            correct = sum(a == b for a, b in zip(expected, provided))
            return {"id": benchmark_id, "correct": correct, "total": len(expected),
                    "score": round(correct / len(expected) * 100), "expected": item["answer"]}
    raise HTTPException(404, "Benchmark not found")


if __name__ == "__main__":
    import argparse
    import uvicorn

    parser = argparse.ArgumentParser(description="Run Benchmark Atlas locally.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8000, type=int)
    parser.add_argument("--no-browser", action="store_true", help="Do not open the dashboard automatically.")
    args = parser.parse_args()
    if not args.no_browser:
        # Delay allows the local server to become reachable before opening the UI.
        import threading
        threading.Timer(1.0, lambda: webbrowser.open(f"http://{args.host}:{args.port}")).start()
    uvicorn.run(app, host=args.host, port=args.port)
