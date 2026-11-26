"""Stage reviewed results in a clean checkout; never publish automatically."""
import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def stage(source, run_id):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,127}", run_id):
        raise ValueError("Invalid run ID")
    data = json.loads(Path(source).read_text(encoding="utf-8"))
    version = data["benchmark_version"]
    if not re.fullmatch(r"[0-9]+[.][0-9]+[.][0-9]+", version):
        raise ValueError("Invalid version")
    target = ROOT / "results" / ("v" + version) / run_id
    target.mkdir(parents=True, exist_ok=False)
    try:
        shutil.copyfile(source, target / "result.json")
        subprocess.run(["python" if __import__("os").name == "nt" else "python3", str(ROOT / "scripts/validate.py")], check=True, cwd=ROOT)
    except BaseException:
        shutil.rmtree(target)
        raise
    return target

def main():
    p = argparse.ArgumentParser()
    p.add_argument("source", type=Path)
    p.add_argument("--run-id", required=True)
    p.add_argument("--reviewed", action="store_true", help="Confirm public JSON has been reviewed and sanitized")
    args = p.parse_args()
    if not args.reviewed:
        p.error("Review and sanitize the JSON before staging")
    print(stage(args.source, args.run_id))
    print("Review git diff and use the submission skill to create a PR after approval.")

if __name__ == "__main__":
    main()
