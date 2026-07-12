"""Benchmark Atlas — self-contained API and web UI."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
import time
import sys
import webbrowser
import os
import re
import threading
import uuid
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
DEFAULT_ATLAS_URL = "https://raw.githubusercontent.com/unaveragetech/benchmark-atlas/master/benchmarks"
DEFAULT_MODEL_ENDPOINT = "http://127.0.0.1:11434/api/chat"
SETTINGS_FILE = Path(os.getenv("APPDATA", Path.home())) / "BenchmarkAtlas" / "settings.json"


def read_settings():
    try:
        return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


saved_settings = read_settings()
REPOSITORY_URL = os.getenv("BENCHMARK_REPOSITORY_URL", saved_settings.get("atlas_url", DEFAULT_ATLAS_URL)).rstrip("/")
MODEL_ENDPOINT = os.getenv("MODEL_ENDPOINT_URL", saved_settings.get("model_endpoint", DEFAULT_MODEL_ENDPOINT)).rstrip("/")
MODEL_NAME = os.getenv("MODEL_NAME", saved_settings.get("model_name", ""))
started = time.time()
api_enabled = True
RUNS = {}
RUNS_LOCK = threading.Lock()

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
    atlas_url: str = DEFAULT_ATLAS_URL
    model_endpoint: str = DEFAULT_MODEL_ENDPOINT
    model_name: str = ""


class CategoryRun(BaseModel):
    category: str


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
    return {"atlas_url": REPOSITORY_URL, "model_endpoint": MODEL_ENDPOINT, "model_name": MODEL_NAME}


@app.post("/api/config")
def update_config(config: ClientConfig):
    global REPOSITORY_URL, MODEL_ENDPOINT, MODEL_NAME
    previous_url = REPOSITORY_URL
    REPOSITORY_URL = config.atlas_url.rstrip("/")
    MODEL_ENDPOINT = config.model_endpoint.rstrip("/")
    MODEL_NAME = config.model_name.strip()
    # Validate the Atlas source immediately, so a bad URL is never silently saved.
    if REPOSITORY_URL:
        try:
            load_benchmarks()
        except Exception as exc:
            REPOSITORY_URL = previous_url
            raise HTTPException(400, f"Could not load Atlas manifest: {exc}")
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps({"atlas_url": REPOSITORY_URL, "model_endpoint": MODEL_ENDPOINT,
                                         "model_name": MODEL_NAME}, indent=2), encoding="utf-8")
    return {"atlas_url": REPOSITORY_URL, "model_endpoint": MODEL_ENDPOINT, "model_name": MODEL_NAME}


@app.get("/api/models")
def models():
    try:
        if "/api/" in MODEL_ENDPOINT:
            base = MODEL_ENDPOINT.split("/api/", 1)[0]
            response = json.loads(urlopen(f"{base}/api/tags", timeout=5).read())
            names = [item["name"] for item in response.get("models", [])]
            details = [{"name": item["name"], "size": item.get("size"),
                        "parameters": item.get("details", {}).get("parameter_size"),
                        "quantization": item.get("details", {}).get("quantization_level"),
                        "family": item.get("details", {}).get("family")} for item in response.get("models", [])]
            provider = "ollama"
        else:
            base = MODEL_ENDPOINT.rsplit("/chat/completions", 1)[0].rstrip("/")
            response = json.loads(urlopen(Request(f"{base}/models", headers={"Accept": "application/json"}), timeout=5).read())
            names = [item["id"] for item in response.get("data", [])]
            details = [{"name": item["id"]} for item in response.get("data", [])]
            provider = "openai-compatible"
        return {"provider": provider, "models": names, "details": details, "selected": MODEL_NAME}
    except Exception as exc:
        if MODEL_NAME:
            return {"provider": "custom-compatible", "models": [MODEL_NAME],
                    "details": [{"name": MODEL_NAME}], "selected": MODEL_NAME,
                    "warning": f"Automatic discovery is unavailable; using the configured model. {exc}"}
        raise HTTPException(502, f"Could not discover models: {exc}")


@app.post("/api/benchmarks/{benchmark_id}/run-model")
def run_model(benchmark_id: str):
    if not MODEL_ENDPOINT:
        raise HTTPException(400, "Set a model endpoint in Client settings first.")
    item = next((x for x in load_benchmarks() if x["id"] == benchmark_id), None)
    if not item:
        raise HTTPException(404, "Benchmark not found")
    if not MODEL_NAME:
        raise HTTPException(400, "Select a model in Client settings first.")
    payload = {"model": MODEL_NAME, "messages": [
        {"role": "system", "content": "Answer every requested item in order as a semicolon-separated list. Do not explain."},
        {"role": "user", "content": item["prompt"]}], "temperature": 0, "stream": False}
    try:
        request = Request(MODEL_ENDPOINT, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"}, method="POST")
        response = json.loads(urlopen(request, timeout=45).read())
        if "message" in response:
            answer = response["message"]["content"].strip()
        else:
            answer = response["choices"][0]["message"]["content"].strip()
    except Exception as exc:
        raise HTTPException(502, f"Model endpoint failed: {exc}")
    return {"answer": answer, "benchmark_id": benchmark_id}


def call_model(item):
    if not MODEL_ENDPOINT or not MODEL_NAME:
        raise RuntimeError("Configure and select a model first.")
    payload = {"model": MODEL_NAME, "messages": [
        {"role": "system", "content": "Answer only with the requested fact. Do not explain."},
        {"role": "user", "content": item["prompt"]}], "temperature": 0, "stream": False}
    request = Request(MODEL_ENDPOINT, data=json.dumps(payload).encode(),
                      headers={"Content-Type": "application/json"}, method="POST")
    response = json.loads(urlopen(request, timeout=90).read())
    return (response["message"]["content"] if "message" in response
            else response["choices"][0]["message"]["content"]).strip()


def run_category_job(run_id, category):
    items = [item for item in load_benchmarks() if item["category"].casefold() == category.casefold()]
    with RUNS_LOCK:
        RUNS[run_id].update(total=len(items), status="running")
    for index, item in enumerate(items, 1):
        with RUNS_LOCK:
            if RUNS[run_id].get("cancel_requested"):
                RUNS[run_id]["status"] = "cancelled"
                RUNS[run_id]["finished_at"] = datetime.now(timezone.utc).isoformat()
                return
        question_started = time.perf_counter()
        try:
            response = call_model(item)
            expected = [value.strip().casefold() for value in item["answer"]]
            provided = [value.strip().casefold() for value in re.split(r"[;\n,]+", response) if value.strip()]
            correct = sum(a == b for a, b in zip(expected, provided))
            result = {"id": item["id"], "prompt": item["prompt"], "response": response,
                      "expected": item["answer"], "score": round(correct / len(expected) * 100),
                      "latency_ms": round((time.perf_counter() - question_started) * 1000)}
        except Exception as exc:
            result = {"id": item["id"], "prompt": item["prompt"], "response": "",
                      "expected": item["answer"], "score": 0, "error": str(exc),
                      "latency_ms": round((time.perf_counter() - question_started) * 1000)}
        with RUNS_LOCK:
            job = RUNS[run_id]
            job["results"].append(result)
            job["completed"] = index
            job["score"] = round(sum(row["score"] for row in job["results"]) / index)
            job["correct"] = sum(row["score"] == 100 for row in job["results"])
            job["incorrect"] = index - job["correct"]
            job["average_latency_ms"] = round(sum(row["latency_ms"] for row in job["results"]) / index)
            elapsed = max(time.time() - job["started_epoch"], 0.001)
            job["questions_per_minute"] = round(index / elapsed * 60, 1)
    with RUNS_LOCK:
        RUNS[run_id]["status"] = "complete"
        RUNS[run_id]["finished_at"] = datetime.now(timezone.utc).isoformat()


@app.post("/api/runs")
def start_category_run(request: CategoryRun):
    categories = {item["category"].casefold(): item["category"] for item in load_benchmarks()}
    category = categories.get(request.category.casefold())
    if not category:
        raise HTTPException(404, "Category not found")
    if not MODEL_NAME:
        raise HTTPException(400, "Select a model in Client settings first.")
    run_id = uuid.uuid4().hex
    RUNS[run_id] = {"id": run_id, "category": category, "model": MODEL_NAME, "status": "queued",
                    "completed": 0, "total": 0, "score": 0, "correct": 0, "incorrect": 0,
                    "average_latency_ms": 0, "questions_per_minute": 0, "results": [],
                    "started_at": datetime.now(timezone.utc).isoformat(), "started_epoch": time.time(),
                    "finished_at": None, "cancel_requested": False}
    threading.Thread(target=run_category_job, args=(run_id, category), daemon=True).start()
    return RUNS[run_id]


@app.get("/api/runs/{run_id}")
def category_run_status(run_id: str):
    if run_id not in RUNS:
        raise HTTPException(404, "Run not found")
    return RUNS[run_id]


@app.get("/api/runs")
def run_history():
    runs = sorted(RUNS.values(), key=lambda item: item["started_at"], reverse=True)
    return {"count": len(runs), "items": runs}


@app.delete("/api/runs/{run_id}")
def cancel_category_run(run_id: str):
    if run_id not in RUNS:
        raise HTTPException(404, "Run not found")
    RUNS[run_id]["cancel_requested"] = True
    return {"id": run_id, "status": "cancelling"}


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
            separator = r"[;\n]+" if ";" in submission.answer or "\n" in submission.answer else r","
            provided = [x.strip().casefold() for x in re.split(separator, submission.answer) if x.strip()]
            correct = sum(a == b for a, b in zip(expected, provided))
            return {"id": benchmark_id, "correct": correct, "total": len(expected),
                    "score": round(correct / len(expected) * 100), "expected": item["answer"]}
    raise HTTPException(404, "Benchmark not found")


if __name__ == "__main__":
    import argparse
    import uvicorn

    # Windowed PyInstaller builds expose no stdout/stderr. Give libraries safe
    # sinks so their startup diagnostics never crash the app process.
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w", encoding="utf-8")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w", encoding="utf-8")

    parser = argparse.ArgumentParser(description="Run Benchmark Atlas locally.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8000, type=int)
    parser.add_argument("--no-browser", action="store_true", help="Do not open the dashboard automatically.")
    args = parser.parse_args()
    if not args.no_browser:
        # Delay allows the local server to become reachable before opening the UI.
        import threading
        threading.Timer(1.0, lambda: webbrowser.open(f"http://{args.host}:{args.port}")).start()
    # Disable console logging so the packaged windowless launcher can run without
    # a command window while continuing to serve the browser dashboard.
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_config={"version": 1, "disable_existing_loggers": False},
        access_log=False,
    )
