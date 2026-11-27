import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
version = (root / "VERSION").read_text(encoding="utf-8").strip()
folder = root / "benchmarks" / ("v" + version)
manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
assert manifest["version"] == version
cases = manifest["cases"]
assert len({c["id"] for c in cases}) == len(cases)
assert sum(c["weight"] for c in cases) == 100
skill = (root / "skills/llm-benchmark/SKILL.md").read_text(encoding="utf-8")
for c in cases:
    prompt = (folder / c["prompt"]).read_text(encoding="utf-8").strip()
    assert prompt and prompt in skill, c["id"]
    assert c["weight"] >= 0
    assert c["time_limit_seconds"] is None or c["time_limit_seconds"] > 0
for p in (root / "results").glob("v*/*/result.json"):
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data["benchmark_version"] == p.parent.parent.name[1:]
    m = json.loads((root / "benchmarks" / p.parent.parent.name / "manifest.json").read_text(encoding="utf-8"))
    ids = {c["id"] for c in m["cases"]}
    assert data["model"] and isinstance(data["cases"], list)
    assert len({row["case_id"] for row in data["cases"]}) == len(data["cases"])
    weights = {c["id"]: c["weight"] for c in m["cases"]}
    for row in data["cases"]:
        score = row.get("score")
        assert score is None or (type(score) in (int, float) and 0 <= score <= (weights[row["case_id"]] or 100))
        if score is not None:
            assert row.get("evaluation_type") in ("self", "independent")
        speed = row.get("generation_tokens_per_second")
        assert speed is None or (type(speed) in (int, float) and speed >= 0)
        assert row["case_id"] in ids
        for key in ("elapsed_seconds", "ttft_seconds", "input_tokens", "output_tokens"):
            v = row[key]
            assert v is None or (type(v) in (int, float) and v >= 0)
print("Validation passed")
