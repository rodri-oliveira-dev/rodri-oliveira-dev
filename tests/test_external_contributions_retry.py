"""Deterministic retry/rate-limit tests for both curated and discovery collectors."""

import io
import json
import tempfile
import unittest
from pathlib import Path
from urllib.error import HTTPError, URLError

from scripts.discover_external_contributions import discover
from scripts.external_contributions import CollectionError, GitHubAPI, collect, write_snapshot


def curated():
    return {
        "schema_version": 1,
        "profile": "rodri-oliveira-dev",
        "projects": [{
            "repository": "SomeOrg/SomeProject",
            "name": "External project",
            "pull_requests": [{"number": 10, "pt": "Texto", "en": "Text"}],
        }],
    }


def discovery_config():
    return curated()


class Clock:
    def __init__(self):
        self.now = 1000.0
        self.waits = []

    def sleep(self, seconds):
        self.waits.append(seconds)
        self.now += seconds

    def monotonic(self):
        return self.now

    def wall_time(self):
        return self.now


class Response:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_):
        pass

    def read(self):
        return self.payload


class Opener:
    def __init__(self, *responses, clock=None, request_elapsed=0.0):
        self.responses = list(responses)
        self.requests = []
        self.clock = clock
        self.request_elapsed = request_elapsed

    def __call__(self, request, timeout):
        self.requests.append((request, timeout))
        if self.clock is not None:
            self.clock.now += self.request_elapsed
        if not self.responses:
            raise AssertionError("Unexpected extra API request")
        response = self.responses.pop(0)
        if isinstance(response, BaseException):
            raise response
        return Response(response)


def http(code, headers=None, body=b"secret-response"):
    return HTTPError("https://api.github.com/search/issues?token=private", code,
                     "not for logs", headers or {}, io.BytesIO(body))


class RetryTests(unittest.TestCase):
    def api(self, responses, **options):
        clock = options.pop("clock", Clock())
        opener = Opener(*responses, clock=clock)
        api = GitHubAPI(
            "secret-token", opener=opener, sleep=clock.sleep,
            monotonic=clock.monotonic, wall_time=clock.wall_time,
            jitter=lambda: 0.0, **options,
        )
        return api, clock, opener

    def test_429_retry_after_seconds_then_success(self):
        api, clock, opener = self.api([
            http(429, {"Retry-After": "3"}),
            b'{"items":[],"total_count":0,"incomplete_results":false}',
        ])
        self.assertEqual(api.get("/search/issues", {"q": "public"})["total_count"], 0)
        self.assertEqual(clock.waits, [3.0])
        self.assertEqual(len(opener.requests), 2)
        self.assertTrue(all(timeout <= 10 for _, timeout in opener.requests))

    def test_429_rate_reset_when_retry_after_missing(self):
        api, clock, opener = self.api([
            http(429, {"X-RateLimit-Reset": "1007"}),
            b'{"ok":true}',
        ])
        self.assertTrue(api.get("/search/issues", {})["ok"])
        self.assertEqual(clock.waits, [7.0])
        self.assertEqual(len(opener.requests), 2)

    def test_retry_after_http_date(self):
        api, clock, _ = self.api([
            http(503, {"Retry-After": "Thu, 01 Jan 1970 00:16:45 GMT"}),
            b'{"ok":true}',
        ])
        self.assertTrue(api.get("/search/issues", {})["ok"])
        self.assertEqual(clock.waits, [5.0])

    def test_503_and_network_error_then_success_use_progressive_wait(self):
        api, clock, opener = self.api([
            http(503),
            URLError("connection dropped"),
            b'{"ok":true}',
        ])
        self.assertTrue(api.get("/search/issues", {})["ok"])
        self.assertEqual(clock.waits, [1.0, 2.0])
        self.assertEqual(len(opener.requests), 3)

    def test_transient_timeouts_exhaust_attempts_without_partial_snapshot(self):
        api, clock, opener = self.api([TimeoutError("timeout")] * 3)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "snapshot.json"
            output.write_text('{"last":"valid"}\n', encoding="utf-8")
            with self.assertRaisesRegex(CollectionError, "retry limit"):
                write_snapshot(output, collect(curated(), api))
            self.assertEqual(output.read_text(encoding="utf-8"), '{"last":"valid"}\n')
        self.assertEqual(clock.waits, [1.0, 2.0])
        self.assertEqual(len(opener.requests), 3)

    def test_401_403_and_400_are_not_retried(self):
        for code in (400, 401, 403):
            with self.subTest(code=code):
                api, clock, opener = self.api([http(code)])
                with self.assertRaisesRegex(CollectionError, f"HTTP {code}") as raised:
                    api.get("/search/issues", {"q": "test"})
                self.assertNotIn("secret", str(raised.exception))
                self.assertNotIn("api.github.com", str(raised.exception))
                self.assertEqual(len(opener.requests), 1)
                self.assertEqual(clock.waits, [])

    def test_429_retry_after_beyond_budget_fails_without_premature_retry(self):
        api, clock, opener = self.api([http(429, {"Retry-After": "120"})])
        with self.assertRaisesRegex(CollectionError, "time budget"):
            api.get("/search/issues", {})
        self.assertEqual(clock.waits, [])
        self.assertEqual(len(opener.requests), 1)

    def test_reset_beyond_budget_fails_without_premature_retry(self):
        api, clock, opener = self.api([http(429, {"X-RateLimit-Reset": "1200"})])
        with self.assertRaisesRegex(CollectionError, "time budget"):
            api.get("/search/issues", {})
        self.assertEqual(clock.waits, [])
        self.assertEqual(len(opener.requests), 1)

    def test_total_wait_budget_restricts_retry(self):
        api, clock, opener = self.api([
            http(503, {"Retry-After": "7"}),
            http(503, {"Retry-After": "7"}),
            b'{"should_not":"return"}',
        ], max_total_wait=10)
        with self.assertRaisesRegex(CollectionError, "time budget"):
            api.get("/search/issues", {})
        self.assertEqual(clock.waits, [7.0])
        self.assertEqual(len(opener.requests), 2)

    def test_elapsed_budget_includes_network_duration(self):
        clock = Clock()
        opener = Opener(http(503), clock=clock, request_elapsed=4)
        api = GitHubAPI(
            "secret-token", opener=opener, timeout=4,
            max_elapsed=4, max_total_wait=3, sleep=clock.sleep,
            monotonic=clock.monotonic, jitter=lambda: 0.0,
        )
        with self.assertRaisesRegex(CollectionError, "time budget"):
            api.get("/search/issues", {})
        self.assertEqual(clock.waits, [])

    def test_malformed_json_does_not_retry(self):
        api, clock, opener = self.api([b'not-json', b'{"ok":true}'])
        with self.assertRaisesRegex(CollectionError, "request or response failed"):
            api.get("/search/issues", {})
        self.assertEqual(len(opener.requests), 1)
        self.assertEqual(clock.waits, [])

    def test_max_attempts_one_never_waits(self):
        api, clock, opener = self.api([http(429)], max_attempts=1)
        with self.assertRaisesRegex(CollectionError, "retry limit"):
            api.get("/search/issues", {})
        self.assertEqual(len(opener.requests), 1)
        self.assertEqual(clock.waits, [])

    def test_bad_retry_configuration_rejected(self):
        for config in (
            {"max_attempts": 0}, {"max_attempts": 5},
            {"max_total_wait": 100}, {"timeout": 0},
            {"max_elapsed": -1},
        ):
            with self.subTest(config=config):
                with self.assertRaises(ValueError):
                    GitHubAPI("token", **config)

    def test_discovery_uses_the_same_retried_client(self):
        login = "rodri-oliveira-dev"
        payload = {
            "total_count": 1,
            "incomplete_results": False,
            "items": [{
                "repository_url": "https://api.github.com/repos/External/NewProject",
                "user": {"login": login},
                "number": 31, "state": "open",
                "pull_request": {"merged_at": None},
            }],
        }
        api, clock, opener = self.api([http(503), json.dumps(payload).encode()])
        result = discover(discovery_config(), api)
        self.assertEqual(result["candidate_repositories"][0]["repository"], "External/NewProject")
        self.assertEqual(len(opener.requests), 2)
        self.assertEqual(clock.waits, [1.0])


if __name__ == "__main__":
    unittest.main()
