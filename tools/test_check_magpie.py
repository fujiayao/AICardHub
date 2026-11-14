from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("check_magpie", Path(__file__).with_name("check_magpie.py"))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class Response:
    status = 200
    def read(self, maximum):
        return json.dumps({"data": [{"id": "gpt-demo"}, {"id": "deepseek-demo"}]}).encode()

class Connection:
    def __init__(self, *args, **kwargs):
        self.calls = []
    def request(self, method, path, headers):
        self.calls.append((method, path))
    def getresponse(self):
        return Response()
    def close(self):
        pass

class Tests(unittest.TestCase):
    def test_reject_nonlocal_and_credentials(self):
        for url in ("https://127.0.0.1:3425", "http://example.com", "http://127.0.0.1.evil.test", "http://user:secret@localhost:3425", "http://localhost:3425/path", "http://localhost?key=secret"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                module.check(url)

    def test_metadata_only_and_no_raw_body(self):
        made = []
        def factory(*args, **kwargs):
            c = Connection(*args, **kwargs)
            made.append(c)
            return c
        with patch.object(module.http.client, "HTTPConnection", side_effect=factory):
            result = module.check("http://127.0.0.1:3425")
        self.assertEqual([c.calls[0] for c in made], [("GET", "/health"), ("GET", "/v1/models")])
        models = result["requests"]["/v1/models"]
        self.assertEqual(models["model_count"], 2)
        self.assertEqual(models["id_family_hints"]["deepseek"], 1)
        self.assertNotIn("gpt-demo", json.dumps(result))

    def test_connection_error_is_redacted(self):
        with patch.object(module.http.client, "HTTPConnection", side_effect=OSError("secret body")):
            # Constructor errors should remain errors, not be interpreted as success.
            with self.assertRaises(OSError):
                module.check("http://localhost:3425")
        class Refused(Connection):
            def request(self, *args, **kwargs):
                raise ConnectionRefusedError("secret body")
        with patch.object(module.http.client, "HTTPConnection", Refused):
            result = module.check("http://localhost:3425")
        self.assertEqual(result["requests"]["/health"]["error_type"], "ConnectionRefusedError")
        self.assertNotIn("secret body", json.dumps(result))

if __name__ == "__main__":
    unittest.main()
