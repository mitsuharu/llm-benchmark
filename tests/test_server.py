import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
from scripts.server import server

class ServerTests(unittest.TestCase):
    def test_cleanup(self):
        with tempfile.TemporaryDirectory() as tmp:
            binary = Path(tmp) / "llama-server"
            model = Path(tmp) / "model.gguf"
            binary.touch()
            model.touch()
            with patch("scripts.server.subprocess.Popen") as popen, patch("scripts.server.urllib.request.urlopen") as urlopen:
                proc = popen.return_value
                proc.poll.return_value = None
                urlopen.return_value.__enter__.return_value.status = 200
                with self.assertRaises(ValueError):
                    with server(binary, model, 4096, 99) as (url, startup):
                        self.assertTrue(url.endswith("/v1"))
                        raise ValueError("test")
                proc.terminate.assert_called_once()
                proc.wait.assert_called_once_with(timeout=5)
