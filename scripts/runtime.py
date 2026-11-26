"""Install a pinned llama.cpp release archive after verifying its SHA-256."""
import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import tempfile
import urllib.request
import zipfile
from pathlib import Path

def sha256(path):
    with Path(path).open("rb") as f:
        digest = hashlib.sha256()
        for block in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(block)
        return digest.hexdigest()

def extract(archive, target):
    with zipfile.ZipFile(archive) as z:
        for entry in z.infolist():
            dest = (target / entry.filename).resolve()
            if not dest.is_relative_to(target.resolve()) or stat.S_ISLNK(entry.external_attr >> 16):
                raise ValueError("Unsafe archive entry")
            z.extract(entry, target)
            mode = (entry.external_attr >> 16) & 0o777
            if mode and not entry.is_dir():
                dest.chmod(mode)

def prepare(version, asset, checksum, cache):
    if not re.fullmatch(r"b[0-9]+", version) or not re.fullmatch(r"[A-Za-z0-9_.-]+\.zip", asset):
        raise ValueError("Specify a pinned build and exact ZIP asset name")
    if not re.fullmatch(r"[a-fA-F0-9]{64}", checksum):
        raise ValueError("Expected SHA-256 is required")
    target = Path(cache).expanduser() / "llama.cpp" / version / asset
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        metadata = json.loads((target / "runtime.json").read_text())
        if metadata["archive_sha256"] != checksum.lower():
            raise ValueError("Cached archive checksum differs")
        binary = target / metadata["binary"]
        if sha256(binary) != metadata["binary_sha256"]:
            raise ValueError("Cached executable checksum differs")
        return binary
    with tempfile.TemporaryDirectory(dir=target.parent) as tmp:
        work = Path(tmp)
        archive = work / "release.zip"
        url = f"https://github.com/ggml-org/llama.cpp/releases/download/{version}/{asset}"
        with urllib.request.urlopen(url, timeout=60) as response, archive.open("wb") as out:
            shutil.copyfileobj(response, out)
        if sha256(archive) != checksum.lower():
            raise ValueError("Archive checksum mismatch")
        unpacked = work / "unpacked"
        unpacked.mkdir()
        extract(archive, unpacked)
        binaries = [p for p in unpacked.rglob("*") if p.is_file() and p.name in ("llama-server", "llama-server.exe")]
        if len(binaries) != 1:
            raise ValueError("Expected exactly one llama-server executable")
        binary = binaries[0]
        relative = binary.relative_to(unpacked)
        metadata = dict(version=version, asset=asset, archive_sha256=checksum.lower(), binary=str(relative), binary_sha256=sha256(binary))
        (unpacked / "runtime.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        unpacked.rename(target)
    return target / relative

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--version", required=True)
    p.add_argument("--asset", required=True)
    p.add_argument("--sha256", required=True)
    p.add_argument("--cache", default=os.environ.get("LLM_BENCHMARK_CACHE", str(Path.home() / ".cache" / "llm-benchmark" / "runtimes")))
    args = p.parse_args()
    print(prepare(args.version, args.asset, args.sha256, args.cache))

if __name__ == "__main__":
    main()
