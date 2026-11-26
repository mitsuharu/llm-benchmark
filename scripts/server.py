"""Lifecycle management for a local llama-server."""
import contextlib
import socket
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path

@contextlib.contextmanager
def server(binary, model, context, gpu_layers, startup_timeout=180):
    binary = Path(binary).resolve(strict=True)
    model = Path(model).resolve(strict=True)
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    base = f"http://127.0.0.1:{port}"
    args = [str(binary), "-m", str(model), "--host", "127.0.0.1",
            "--port", str(port), "-c", str(context), "-ngl", str(gpu_layers)]
    with tempfile.TemporaryFile() as log:
        proc = subprocess.Popen(args, stdout=log, stderr=log, cwd=binary.parent)
        start = time.monotonic()
        try:
            while time.monotonic() - start < startup_timeout:
                if proc.poll() is not None:
                    raise RuntimeError("llama-server exited during startup")
                try:
                    with urllib.request.urlopen(base + "/health", timeout=1) as response:
                        if response.status == 200 and proc.poll() is None:
                            break
                except OSError:
                    pass
                time.sleep(0.25)
            else:
                raise TimeoutError("llama-server startup timed out")
            yield base + "/v1", time.monotonic() - start
        finally:
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()
