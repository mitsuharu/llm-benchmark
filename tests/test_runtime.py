import tempfile
import unittest
import zipfile
from pathlib import Path
from scripts.runtime import extract, sha256, prepare

class RuntimeTests(unittest.TestCase):
    def test_sha256(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "file"
            p.write_bytes(b"abc")
            self.assertEqual(sha256(p), "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")
    def test_traversal(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "bad.zip"
            with zipfile.ZipFile(p, "w") as z:
                z.writestr("../escape", "bad")
            with self.assertRaises(ValueError):
                extract(p, Path(tmp) / "target")
    def test_unpinned(self):
        with self.assertRaises(ValueError):
            prepare("latest", "release.zip", "a"*64, ".")
