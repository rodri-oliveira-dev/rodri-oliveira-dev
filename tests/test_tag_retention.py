"""Tests for profile tag retention (no network access)."""

import os
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from scripts import tag_retention as retention


NOW = datetime(2026, 10, 28, 12, 0, tzinfo=timezone.utc)


def release(tag, published_at, **extra):
    return {"tag_name": tag, "published_at": published_at, **extra}


def refs(*names):
    return [{"ref": "refs/tags/" + name} for name in names]


class TagRetentionTests(unittest.TestCase):
    def test_subtracts_calendar_months_and_clamps_end_of_month(self):
        self.assertEqual(retention.subtract_months(
            datetime(2026, 5, 31, tzinfo=timezone.utc), 3
        ), datetime(2026, 2, 28, tzinfo=timezone.utc))
        self.assertEqual(retention.subtract_months(
            datetime(2024, 3, 31, tzinfo=timezone.utc), 1
        ), datetime(2024, 2, 29, tzinfo=timezone.utc))

    def test_only_expired_published_tags_are_selected(self):
        rows = [
            release("v1.0.1", "2026-07-27T12:00:00Z"),
            release("v1.0.2", "2026-07-28T12:00:00Z"),
            release("v1.0.3", "2026-10-28T12:00:00Z"),
        ]
        self.assertEqual(
            retention.find_expired_tags(refs("v1.0.1", "v1.0.2", "v1.0.3"), rows, NOW),
            [("v1.0.1", "2026-07-27T12:00:00Z")],
        )

    def test_latest_semver_is_protected_even_when_old(self):
        rows = [
            release("v1.0.9", "2026-01-01T00:00:00Z"),
            release("v1.0.10", "2026-02-01T00:00:00Z"),
        ]
        self.assertEqual(
            retention.find_expired_tags(refs("v1.0.9", "v1.0.10"), rows, NOW),
            [("v1.0.9", "2026-01-01T00:00:00Z")],
        )

    def test_skips_unreleased_draft_immutable_and_unmanaged_tags(self):
        rows = [
            release("v1.0.1", "2026-01-01T00:00:00Z", draft=True),
            release("v1.0.2", "2026-01-01T00:00:00Z", immutable=True),
            release("legacy", "2026-01-01T00:00:00Z"),
            release("v1.0.3", "2026-01-01T00:00:00Z"),
            release("v1.0.4", "2026-09-01T00:00:00Z"),
            release("v1.0.5", "2026-10-01T00:00:00Z"),
        ]
        actual = retention.find_expired_tags(
            refs("v1.0.1", "v1.0.2", "legacy", "v1.0.3", "v1.0.5", "unreleased-v1"), rows, NOW
        )
        self.assertEqual(actual, [("v1.0.3", "2026-01-01T00:00:00Z")])

    def test_dry_run_never_deletes(self):
        rows = [
            release("v1.0.1", "2026-01-01T00:00:00Z"),
            release("v1.0.2", "2026-10-01T00:00:00Z"),
        ]
        with patch.dict(os.environ, {"GITHUB_REPOSITORY": "a/repo", "GH_TOKEN": "test"}, clear=True), \
             patch.object(retention, "github_api", side_effect=[
                 refs("v1.0.1", "v1.0.2"), rows,
             ]) as api:
            self.assertEqual(retention.run(dry_run=True, now=NOW), 1)
            self.assertEqual(api.call_count, 2)
            self.assertTrue(all(call.kwargs.get("method", "GET") == "GET" for call in api.call_args_list))

    def test_deletion_targets_only_validated_tag_ref(self):
        rows = [
            release("v1.0.1", "2026-01-01T00:00:00Z"),
            release("v1.0.2", "2026-10-01T00:00:00Z"),
        ]
        with patch.dict(os.environ, {"GITHUB_REPOSITORY": "a/repo", "GH_TOKEN": "test"}, clear=True), \
             patch.object(retention, "github_api", side_effect=[
                 refs("v1.0.1", "v1.0.2"), rows, None,
             ]) as api:
            self.assertEqual(retention.run(dry_run=False, now=NOW), 1)
            self.assertEqual(
                api.call_args_list[-1].args,
                ("a/repo", "test", "/git/refs/tags/v1.0.1"),
            )
            self.assertEqual(api.call_args_list[-1].kwargs, {"method": "DELETE"})

    def test_pagination_loads_all_release_pages(self):
        items = [release("v1.0.1", "2026-01-01T00:00:00Z")] * 100
        with patch.object(retention, "github_api", side_effect=[items, []]) as api:
            self.assertEqual(len(retention.list_releases("a/repo", "test")), 100)
            self.assertIn("page=2", api.call_args_list[-1].args[-1])

    def test_current_releases_need_no_deletions(self):
        rows = [release(f"v1.0.{n}", "2026-09-17T19:55:12Z") for n in range(32)]
        self.assertEqual(
            retention.find_expired_tags(refs(*(row["tag_name"] for row in rows)), rows, NOW),
            [],
        )


if __name__ == "__main__":
    unittest.main()
