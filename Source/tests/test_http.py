import http.client
import json
import sys
import threading
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app


class HTTPTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        app.DEMO = True
        cls.server = app.ThreadingHTTPServer(("127.0.0.1", 0), app.Handler)
        cls.port = cls.server.server_port
        app.ORIGIN = "http://127.0.0.1:" + str(cls.port)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def request(self, method, path, data=None, headers=None):
        c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=3)
        c.request(method, path, body=data, headers=headers or {})
        r = c.getresponse()
        result = (r.status, r.read(), r.headers)
        c.close()
        return result

    def test_static(self):
        (code, body, headers) = self.request("GET", "/")
        self.assertEqual(code, 200)
        self.assertIn(b"Bootpd Web", body)
        self.assertIn("frame-ancestors 'none'", headers["Content-Security-Policy"])

    def test_host_block(self):
        self.assertEqual(
            self.request("GET", "/", headers={"Host": "evil.test"})[0], 403
        )

    def test_requires_token_and_origin(self):
        self.assertEqual(self.request("POST", "/api", '{"op":"status"}')[0], 403)
        self.assertEqual(
            self.request(
                "POST",
                "/api",
                '{"op":"status"}',
                {"X-Session": app.TOKEN, "Origin": "https://evil.test"},
            )[0],
            403,
        )

    def test_demo_api(self):
        headers = {"Origin": app.ORIGIN, "X-Session": app.TOKEN}
        (code, body, _) = self.request("POST", "/api", '{"op":"status"}', headers)
        self.assertEqual(code, 200)
        self.assertTrue(json.loads(body)["demo"])
        self.assertEqual(
            self.request("POST", "/api", '{"op":"start"}', headers)[0], 400
        )

    def test_path_traversal(self):
        self.assertEqual(self.request("GET", "/../helper.py")[0], 404)


if __name__ == "__main__":
    unittest.main()
