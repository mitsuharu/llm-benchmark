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
import multiprocessing
import hashlib
import statistics
import re
import math
from pathlib import Path

if __package__:
    from .hardware import detect
else:
    from hardware import detect

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
    checks["host"] = detect()
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
                    if status != "truncated":
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

def worker(conn, params):
    try:
        conn.send(measure(*params))
    finally:
        conn.close()

def bounded_measure(*params):
    timeout = params[3]
    ctx = multiprocessing.get_context("spawn")
    receiver, sender = ctx.Pipe(duplex=False)
    process = ctx.Process(target=worker, args=(sender, params))
    start = time.monotonic()
    process.start()
    sender.close()
    try:
        if receiver.poll(max(0, timeout - (time.monotonic() - start))):
            try:
                return receiver.recv()
            except EOFError:
                status = "error"
        else:
            status = "timeout"
        return "", dict(elapsed_seconds=time.monotonic()-start, ttft_seconds=None,
            input_tokens=None, output_tokens=None, prompt_tokens_per_second=None,
            generation_tokens_per_second=None, score=None, evaluation_type=None, status=status)
    finally:
        receiver.close()
        if process.is_alive():
            process.terminate()
        process.join(2)
        if process.is_alive():
            process.kill()
            process.join()

def run(args):
    if args.server_binary or args.auto_prepare:
        if __package__:
            from .server import server
            from .runtime import prepare
        else:
            from server import server
            from runtime import prepare
        binary = args.server_binary
        if args.auto_prepare:
            binary = prepare(args.runtime_version, args.asset, args.archive_sha256, args.cache)
        args.runtime = "llamacpp"
        args.runtime_version = command(str(Path(binary).resolve()), "--version") or args.runtime_version
        with server(binary, args.model_file, args.context_length, args.gpu_layers, args.startup_timeout) as (url, startup):
            args.base_url = url
            args.startup_seconds = startup
            return run_cases(args)
    return run_cases(args)

def run_cases(args):
    version = args.version or (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    if not re.fullmatch(r"[0-9]+[.][0-9]+[.][0-9]+", version):
        raise SystemExit("Invalid benchmark version")
    folder = ROOT / "benchmarks" / ("v" + version)
    cases = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))["cases"]
    if args.case:
        cases = [c for c in cases if c["id"] == args.case]
    if not cases:
        raise SystemExit("Unknown case")
    out = ROOT / "local-runs" / uuid.uuid4().hex
    out.mkdir(parents=True)
    result = dict(benchmark_version=version, benchmark_commit=command("git", "-C", str(ROOT), "rev-parse", "HEAD"),
        runner_version="0.2.0", model=args.model, quantization=args.quantization, gpu=args.gpu,
        runtime=args.runtime, runtime_version=args.runtime_version, backend=args.backend,
        environment=detect(), environment_scope="runner_host",
        settings={"temperature": args.temperature, "context_length": args.context_length, "max_tokens": args.max_tokens, "gpu_layers": args.gpu_layers if args.server_binary or args.auto_prepare else None}, cases=[], startup_seconds=getattr(args, "startup_seconds", None))
    if args.model_file:
        with args.model_file.open("rb") as stream:
            digest = hashlib.sha256()
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
        result["model_sha256"] = digest.hexdigest()
    for case in cases:
        prompt = (folder / case["prompt"]).read_text(encoding="utf-8")
        rows = []
        for i in range(args.repeat):
            answer, row = bounded_measure(args.base_url, args.model, prompt, case["time_limit_seconds"] or args.timeout, args.temperature, args.max_tokens)
            (out / f"{case['id']}-{i+1}.md").write_text(answer, encoding="utf-8")
            rows.append(row)
            (out / f"{case['id']}-repeats.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
        aggregate = dict(rows[0])
        for key in ("elapsed_seconds", "ttft_seconds", "input_tokens", "output_tokens", "prompt_tokens_per_second", "generation_tokens_per_second"):
            values = [row[key] for row in rows]
            aggregate[key] = statistics.median(values) if all(v is not None for v in values) else None
        aggregate["status"] = rows[0]["status"] if all(row["status"] == rows[0]["status"] for row in rows) else "mixed"
        result["cases"].append(dict(case_id=case["id"], repeat=args.repeat, **aggregate))
        (out / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(out)
    return 0

def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="action", required=True)
    d = sub.add_parser("doctor")
    d.add_argument("--submit", action="store_true")
    r = sub.add_parser("run")
    r.add_argument("--model", required=True)
    mode = r.add_mutually_exclusive_group(required=True)
    mode.add_argument("--base-url")
    mode.add_argument("--server-binary", type=Path)
    mode.add_argument("--auto-prepare", action="store_true")
    r.add_argument("--asset")
    r.add_argument("--archive-sha256")
    r.add_argument("--cache", default=os.environ.get("LLM_BENCHMARK_CACHE", str(Path.home() / ".cache" / "llm-benchmark" / "runtimes")))
    r.add_argument("--gpu-layers", type=int, default=99)
    r.add_argument("--startup-timeout", type=float, default=180)
    for name in ("runtime-version", "backend", "quantization", "gpu", "case"):
        r.add_argument("--" + name)
    r.add_argument("--runtime", default="openai-compatible")
    r.add_argument("--temperature", type=float, default=0)
    r.add_argument("--context-length", type=int)
    r.add_argument("--max-tokens", type=int, default=8192)
    r.add_argument("--timeout", type=float, default=300)
    r.add_argument("--version")
    r.add_argument("--repeat", type=int, default=3)
    r.add_argument("--model-file", type=Path)
    args = parser.parse_args()
    if args.action == "run" and (args.repeat < 1 or args.timeout <= 0 or args.max_tokens < 1):
        parser.error("repeat, timeout and max-tokens must be positive")
    if args.action == "run":
        if not math.isfinite(args.timeout) or not math.isfinite(args.startup_timeout) or args.startup_timeout <= 0:
            parser.error("timeouts must be finite and positive")
        if args.server_binary or args.auto_prepare:
            if not args.model_file or not args.model_file.is_file():
                parser.error("managed mode requires an existing --model-file")
            if args.context_length is None:
                args.context_length = 4096
            if args.context_length < 1:
                parser.error("context-length must be positive")
        if args.auto_prepare and not all((args.runtime_version, args.asset, args.archive_sha256)):
            parser.error("auto-prepare requires runtime-version, asset and archive-sha256")
    return doctor(args.submit) if args.action == "doctor" else run(args)

if __name__ == "__main__":
    sys.exit(main())
