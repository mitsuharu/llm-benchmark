import json
import shutil
from collections import Counter
from pathlib import Path

root = Path(__file__).resolve().parents[1]
out = root / "dist"
out.mkdir(exist_ok=True)
for name in ("index.html", "app.js", "run.html", "run.js"):
    shutil.copyfile(root / "site" / name, out / name)
versions = sorted(p.name[1:] for p in (root / "benchmarks").glob("v*/manifest.json") for p in [p.parent])
runs = []
for p in sorted((root / "results").glob("v*/*/result.json")):
    d = json.loads(p.read_text(encoding="utf-8"))
    benchmark = root / "benchmarks" / ("v" + d["benchmark_version"])
    manifest = json.loads((benchmark / "manifest.json").read_text(encoding="utf-8"))
    weights = {c["id"]: c["weight"] for c in manifest["cases"]}
    # Only independently evaluated scores enter the quality summary.
    scored = [c for c in d["cases"] if c.get("evaluation_type") == "independent" and c.get("score") is not None and weights[c["case_id"]] > 0]
    creative = [c["score"] for c in d["cases"] if c["case_id"] == "creative-01" and c.get("evaluation_type") == "independent" and c.get("score") is not None]
    speeds = [c["generation_tokens_per_second"] for c in d["cases"] if isinstance(c.get("generation_tokens_per_second"), (float, int))]
    detected = (d.get("environment") or {}).get("detected_nvidia_gpus") or []
    counts = Counter(gpu["name"] for gpu in detected if gpu.get("name"))
    detected_gpus = ", ".join(f"{name} ×{count}" if count > 1 else name for name, count in counts.items())
    gpu_label = d.get("gpu") or (f"{detected_gpus}（検出）" if detected_gpus else None)
    run_dir = out / "runs" / p.parent.parent.name / p.parent.name
    run_dir.mkdir(parents=True, exist_ok=True)
    detail_path = (run_dir / "detail.json").relative_to(out).as_posix()
    answers_path = p.with_name("answers.json")
    answers = json.loads(answers_path.read_text(encoding="utf-8")) if answers_path.is_file() else {}
    questions = {case["id"]: case for case in manifest["cases"]}
    details = []
    for row in d["cases"]:
        case = questions[row["case_id"]]
        details.append({
            **row,
            "category": case["category"],
            "max_score": case["weight"] or 100,
            "prompt": (benchmark / case["prompt"]).read_text(encoding="utf-8"),
            "answers": answers.get(case["id"], {}),
        })
    detail = {
        "model": d["model"], "runtime": d.get("runtime"), "runtime_version": d.get("runtime_version"),
        "quantization": d.get("quantization"), "gpu": d.get("gpu"), "backend": d.get("backend"),
        "environment": d.get("environment"), "environment_scope": d.get("environment_scope"),
        "settings": d.get("settings"), "cases": details,
    }
    (out / detail_path).write_text(json.dumps(detail, ensure_ascii=False), encoding="utf-8")
    runs.append(dict(version=d["benchmark_version"], id=p.parent.name, model=d["model"], quantization=d.get("quantization"), gpu=gpu_label, runtime=d.get("runtime"), scored=len(scored), total=sum(w>0 for w in weights.values()), score=sum(c["score"] for c in scored) if scored else None, creative=creative[0] if creative else None, speed=sum(speeds)/len(speeds) if speeds else None, detail=detail_path))
(out / "data.json").write_text(json.dumps(dict(versions=versions, runs=runs), ensure_ascii=False), encoding="utf-8")
