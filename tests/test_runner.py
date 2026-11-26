import unittest
from unittest.mock import patch
from scripts.runner import measure

class StreamTests(unittest.TestCase):
    def test_stream(self):
        class Response(list):
            def __enter__(self): return self
            def __exit__(self, *args): pass
        response = Response([b'data: {"choices":[{"delta":{"content":"hello"}}]}\n',
                             b'data: {"usage":{"prompt_tokens":4,"completion_tokens":1},"choices":[]}\n',
                             b'data: [DONE]\n'])
        with patch("urllib.request.urlopen", return_value=response):
            answer, row = measure("http://localhost/v1", "model", "prompt", 10, 0, 100)
        self.assertEqual(answer, "hello")
        self.assertEqual(row["status"], "completed")
        self.assertEqual(row["input_tokens"], 4)
        self.assertIsNone(row["score"])
        self.assertIsNotNone(row["ttft_seconds"])

if __name__ == "__main__":
    unittest.main()
