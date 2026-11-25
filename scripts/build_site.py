import json
import shutil
from pathlib import Path

root = Path(__file__).resolve().parents[1]
out = root / "dist"
out.mkdir(exist_ok=True)
for name in ("index.html", "app.js"):
    shutil.copyfile(root / "site" / name, out / name)
versions = sorted(p.name[1:] for p in (root / "benchmarks").glob("v*/manifest.json") for p in [p.parent])
runs = []
for p in sorted((root / "results").glob("v*/*/result.json")):
    d = json.loads(p.read_text())
    manifest = json.loads((root / "benchmarks" / ("v" + d["benchmark_version"]) / "manifest.json").read_text())
    weights = {c["id"]: c["weight"] for c in manifest["cases"]}
    # Only independently evaluated scores enter the quality summary.
    scored = [c for c in d["cases"] if c.get("evaluation_type") == "independent" and c.get("score") is not None and weights[c["case_id"]] > 0]
    creative = [c["score"] for c in d["cases"] if c["case_id"] == "creative-01" and c.get("evaluation_type") == "independent" and c.get("score") is not None]
    speeds = [c["generation_tokens_per_second"] for c in d["cases"] if isinstance(c.get("generation_tokens_per_second"), (float, int))]
    runs.append(dict(version=d["benchmark_version"], id=p.parent.name, model=d["model"], quantization=d.get("quantization"), gpu=d.get("gpu"), runtime=d.get("runtime"), scored=len(scored), total=sum(w>0 for w in weights.values()), score=sum(c["score"] for c in scored) if scored else None, creative=creative[0] if creative else None, speed=sum(speeds)/len(speeds) if speeds else None))
(out / "data.json").write_text(json.dumps(dict(versions=versions, runs=runs), ensure_ascii=False), encoding="utf-8")
