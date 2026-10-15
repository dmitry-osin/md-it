"""Offline regression checks for store responses and conditional deployments."""
import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from store_status import EXTENSION_ID, STORE_URL, classify, resolve, run


PUBLISHED = f'''<html><head><title>Markdown-It - Chrome Web Store</title>
<meta property="og:url" content="{STORE_URL}">
<meta name="description" content="Convert pages to Markdown."></head>
<body><button><span>Add to Chrome</span></button></body></html>'''


class StoreStatusTests(unittest.TestCase):
    def test_real_unpublished_response_shape(self):
        url = f"https://chromewebstore.google.com/detail/empty-title/{EXTENSION_ID}?hl=en"
        self.assertEqual(classify(200, url, '<title>Chrome Web Store</title>'), "pending")

    def test_error_redirect(self):
        self.assertEqual(classify(200, STORE_URL + "/error", ""), "pending")

    def test_deleted_or_missing_item(self):
        for code in (404, 410):
            self.assertEqual(classify(code, STORE_URL, ""), "pending")

    def test_explicit_unavailable_page(self):
        self.assertEqual(classify(200, STORE_URL, '<h1>Item not available</h1>'), "pending")

    def test_published_listing(self):
        self.assertEqual(classify(200, STORE_URL, PUBLISHED), "published")

    def test_http_200_alone_is_insufficient(self):
        self.assertEqual(classify(200, STORE_URL, "<title>Chrome Web Store</title>"), "unknown")

    def test_different_extension_is_not_accepted(self):
        self.assertEqual(classify(200, STORE_URL, PUBLISHED.replace(EXTENSION_ID, "a" * 32)), "unknown")

    def test_script_text_is_not_install_button(self):
        html = PUBLISHED.replace('<button><span>Add to Chrome</span></button>', '<script>"Add to Chrome"</script>')
        self.assertEqual(classify(200, STORE_URL, html), "unknown")

    def test_rate_limit_server_errors_and_consent_are_unknown(self):
        for code in (403, 429, 500, 503):
            self.assertEqual(classify(code, STORE_URL, PUBLISHED), "unknown")
        self.assertEqual(classify(200, "https://consent.google.com/", PUBLISHED), "unknown")

    def test_unchanged_schedule_skips_deploy(self):
        for status in ("pending", "published"):
            self.assertEqual(resolve({"status": status}, status, "schedule", True), (status, False))

    def test_status_change_deploys_both_directions(self):
        self.assertEqual(resolve({"status": "pending"}, "published", "schedule", True), ("published", True))
        self.assertEqual(resolve({"status": "published"}, "pending", "schedule", True), ("pending", True))

    def test_failed_check_keeps_published_button(self):
        self.assertEqual(resolve({"status": "published"}, "unknown", "schedule", True), ("published", False))

    def test_schedule_without_baseline_skips(self):
        self.assertEqual(resolve({"status": "pending"}, "published", "schedule", False), ("published", False))

    def test_code_push_always_deploys(self):
        self.assertEqual(resolve({"status": "published"}, "unknown", "push", True), ("published", True))

    def test_full_run_reuses_baseline_on_network_failure(self):
        baseline = {"status": "published", "url": STORE_URL, "checkedAt": "2026-10-15T00:00:00+00:00"}
        responses = [(200, "https://dmitry-osin.github.io/md-it/assets/store-status.json", json.dumps(baseline)), OSError("timeout")]
        with TemporaryDirectory() as directory, patch("store_status.fetch", side_effect=responses), patch.dict("os.environ", {"GITHUB_OUTPUT": ""}), redirect_stdout(StringIO()):
            target = Path(directory) / "status.json"
            snapshot, deploy = run(target, "schedule")
            self.assertEqual(snapshot, baseline)
            self.assertFalse(deploy)
            self.assertEqual(json.loads(target.read_text(encoding="utf-8")), baseline)


if __name__ == "__main__":
    unittest.main()
