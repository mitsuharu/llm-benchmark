import unittest
from unittest.mock import patch
from scripts.hardware import detect

class HardwareTests(unittest.TestCase):
    @patch("scripts.hardware.platform.system", return_value="Other")
    @patch("scripts.hardware.query", return_value="GPU A, 16384, 123.4")
    def test_nvidia(self, query, system):
        result = detect()
        self.assertEqual(result["detected_nvidia_gpus"][0]["vram_bytes"], 16*1024**3)
        self.assertIsNone(result["ram_bytes"])
