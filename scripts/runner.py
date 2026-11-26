"""Local benchmark runner; Python 3.10+, standard library only."""
import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import time
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def command(*args):
    try:
        return subprocess.check_output(args, stderr=subprocess.DEVNULL, timeout=20, text=True).strip()
    except (OSError, subprocess.SubprocessError):
        return None

def doctor(submit=False):
    checks = {"python": sys.version.split()[0], "git": command("git", "--version"),
              "gh": command("gh", "--version"), "disk_free_bytes": shutil.disk_usage(ROOT).free}
    if checks["gh"]:
        checks["github_login"] = command("gh", "api", "user", "--jq", ".login")
        checks["github_permission"] = command("gh", "repo", "view", "mitsuharu/llm-benchmark", "--json", "viewerPermission", "--jq", ".viewerPermission")
    ready = bool(checks["git"] and checks.get("github_login") and checks.get("github_permission") in ("WRITE", "MAINTAIN", "ADMIN"))
    checks["submission_ready"] = ready
    print(json.dumps(checks, ensure_ascii=False, indent=2))
    return 0 if not submit or ready else 1

def measure(base_url, model, prompt, timeout, temperature, max_tokens):
    payload = {"model": model, "messages": [{"role": "user", "content": prompt}],
               "stream": True, "temperature": temperature, "max_tokens": max_tokens}
    headers = {"Content-Type": "application/json"}
    if os.environ.get("BENCHMARK_API_KEY"):
        headers["Authorization"] = "Bearer " + os.environ["BENCHMARK_API_KEY"]
    req = urllib.request.Request(base_url.rstrip("/") + "/chat/completions",
                                 data=json.dumps(payload).encode(), headers=headers)
    start = time.monotonic()
    first = None
    chunks = []
    usage = {}
    timings = {}
    status = "error"
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            for line in response:
                if time.monotonic() - start >= timeout:
                    status = "timeout"
                    break
                if not line.startswith(b"data:"):
                    continue
                data = line[5:].strip()
                if data == b"[DONE]":
                    status = "completed"
                    break
                event = json.loads(data)
                if event.get("error"):
                    break
                usage.update(event.get("usage") or {})
                timings.update(event.get("timings") or {})
                for choice in event.get("choices", []):
                    content = choice.get("delta", {}).get("content")
                    if content:
                        if first is None:
                            first = time.monotonic()
                        chunks.append(content)
                    if choice.get("finish_reason"):
                        status = "completed" if choice["finish_reason"] == "stop" else "truncated"
    except TimeoutError:
        status = "timeout"
    except (OSError, ValueError):
        status = "error"
    elapsed = time.monotonic() - start
    return "".join(chunks), dict(elapsed_seconds=elapsed, ttft_seconds=None if first is None else first-start,
        input_tokens=usage.get("prompt_tokens", timings.get("prompt_n")),
        output_tokens=usage.get("completion_tokens", timings.get("predicted_n")),
        prompt_tokens_per_second=timings.get("prompt_per_second"),
        generation_tokens_per_second=timings.get("predicted_per_second"),
        score=None, evaluation_type=None, status=status)

def run(args):
    version = (ROOT / "VERSION").read_text().strip()
    folder = ROOT / "benchmarks" / ("v" + version)
    cases = json.loads((folder / "manifest.json").read_text())["cases"]
    if args.case:
        cases = [c for c in cases if c["id"] == args.case]
    if not cases:
        raise SystemExit("Unknown case")
    out = ROOT / "local-runs" / uuid.uuid4().hex
    out.mkdir(parents=True)
    result = dict(benchmark_version=version, benchmark_commit=command("git", "-C", str(ROOT), "rev-parse", "HEAD"),
        runner_version="0.1.0", model=args.model, quantization=args.quantization, gpu=args.gpu,
        runtime=args.runtime, runtime_version=args.runtime_version, backend=args.backend,
        environment={"os": platform.system(), "release": platform.release(), "architecture": platform.machine()},
        settings={"temperature": args.temperature, "context_length": args.context_length, "max_tokens": args.max_tokens}, cases=[])
    for case in cases:
        prompt = (folder / case["prompt"]).read_text(encoding="utf-8")
        answer, row = measure(args.base_url, args.model, prompt, case["time_limit_seconds"] or args.timeout, args.temperature, args.max_tokens)
        (out / (case["id"] + ".md")).write_text(answer, encoding="utf-8")
        result["cases"].append(dict(case_id=case["id"], **row))
        (out / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(out)
    return 0

def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="action", required=True)
    d = sub.add_parser("doctor")
    d.add_argument("--submit", action="store_true")
    r = sub.add_parser("run")
    for name in ("model", "base-url"):
        r.add_argument("--" + name, required=True)
    for name in ("runtime-version", "backend", "quantization", "gpu", "case"):
        r.add_argument("--" + name)
    r.add_argument("--runtime", default="openai-compatible")
    r.add_argument("--temperature", type=float, default=0)
    r.add_argument("--context-length", type=int)
    r.add_argument("--max-tokens", type=int, default=8192)
    r.add_argument("--timeout", type=float, default=300)
    args = parser.parse_args()
    return doctor(args.submit) if args.action == "doctor" else run(args)

if __name__ == "__main__":
    sys.exit(main())
