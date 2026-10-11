import io
import unittest
from urllib.error import HTTPError, URLError

from scripts.external_contributions import CollectionError, GitHubAPI


class Response:
    def __enter__(self): return self
    def __exit__(self, *_): return False
    def read(self): return b'{"ok": true}'


class RetryTests(unittest.TestCase):
    def test_retries_rate_limit_and_honors_retry_after(self):
        calls, sleeps = [], []
        def opener(*_args, **_kwargs):
            calls.append(1)
            if len(calls) == 1:
                raise HTTPError("redacted", 429, "rate", {"Retry-After": "2"}, io.BytesIO())
            return Response()
        api = GitHubAPI("secret", opener, sleep=sleeps.append, monotonic=lambda: 0, jitter=lambda: 0)
        self.assertEqual(api.get("/x", {}), {"ok": True})
        self.assertEqual(sleeps, [2.0])

    def test_retry_limit_and_permanent_failures_do_not_leak_token(self):
        def transient(*_args, **_kwargs):
            raise URLError("temporary")
        with self.assertRaises(CollectionError) as caught:
            GitHubAPI("top-secret", transient, sleep=lambda _: None, monotonic=lambda: 0,
                      jitter=lambda: 0).get("/x", {})
        self.assertNotIn("top-secret", str(caught.exception))
        calls = []
        def permanent(*_args, **_kwargs):
            calls.append(1)
            raise HTTPError("redacted", 401, "no", {}, io.BytesIO())
        with self.assertRaisesRegex(CollectionError, "HTTP 401"):
            GitHubAPI("secret", permanent).get("/x", {})
        self.assertEqual(len(calls), 1)


if __name__ == "__main__":
    unittest.main()
