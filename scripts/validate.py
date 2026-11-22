import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
version = (root / "VERSION").read_text().strip()
folder = root / "benchmarks" / ("v" + version)
manifest = json.loads((folder / "manifest.json").read_text())
assert manifest["version"] == version
cases = manifest["cases"]
assert len({c["id"] for c in cases}) == len(cases)
assert sum(c["weight"] for c in cases) == 100
skill = (root / "skills/llm-benchmark/SKILL.md").read_text()
for c in cases:
    prompt = (folder / c["prompt"]).read_text().strip()
    assert prompt and prompt in skill, c["id"]
    assert c["weight"] >= 0
    assert c["time_limit_seconds"] is None or c["time_limit_seconds"] > 0
for p in (root / "results").glob("v*/*/result.json"):
    data = json.loads(p.read_text())
    assert data["benchmark_version"] == p.parent.parent.name[1:]
    m = json.loads((root / "benchmarks" / p.parent.parent.name / "manifest.json").read_text())
    ids = {c["id"] for c in m["cases"]}
    assert data["model"] and isinstance(data["cases"], list)
    for row in data["cases"]:
        assert row["case_id"] in ids
        for key in ("elapsed_seconds", "ttft_seconds", "input_tokens", "output_tokens"):
            v = row[key]
            assert v is None or (type(v) in (int, float) and v >= 0)
print("Validation passed")
