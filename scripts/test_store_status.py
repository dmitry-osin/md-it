"""Offline regression checks for store responses and conditional deployments."""
import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from store_status import EXTENSION_ID, STORE_URL, classify, extract_version, resolve, run, valid_snapshot, valid_version


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
        baseline = {"status": "published", "url": STORE_URL, "version": "3.1.0", "checkedAt": "2026-10-15T00:00:00+00:00"}
        responses = [(200, "https://dmitry-osin.github.io/md-it/assets/store-status.json", json.dumps(baseline)), OSError("timeout")]
        with TemporaryDirectory() as directory, patch("store_status.fetch", side_effect=responses), patch.dict("os.environ", {"GITHUB_OUTPUT": ""}), redirect_stdout(StringIO()):
            target = Path(directory) / "status.json"
            snapshot, deploy = run(target, "schedule")
            self.assertEqual(snapshot, baseline)
            self.assertFalse(deploy)
            self.assertEqual(json.loads(target.read_text(encoding="utf-8")), baseline)

    def test_extract_version_from_details_without_css_class_dependencies(self):
        html = '<section><h2>Details</h2><ul><li><div>Version</div><div>2.14.7</div></li></ul></section>'
        self.assertEqual(extract_version(html), "2.14.7")

    def test_description_and_scripts_are_not_release_metadata(self):
        html = '<section><h2>Overview</h2><li>Version<span>9.9.9</span></li></section><script>Version 7.7.7</script>'
        self.assertIsNone(extract_version(html))
        html += '<section><h2>Details</h2><li><div>Version</div><div>4.2</div></li></section>'
        self.assertEqual(extract_version(html), "4.2")

    def test_missing_version_is_not_replaced_with_a_default(self):
        self.assertIsNone(extract_version(PUBLISHED))

    def test_version_validation(self):
        for version in ("1", "0.1", "2.0.17", "65535.0.1.4"):
            self.assertTrue(valid_version(version), version)
        for version in (None, 3, "", "0", "0.0.0", "01.2", "1.2.3.4.5", "65536.1", "1.2-beta", "<script>"):
            self.assertFalse(valid_version(version), repr(version))

    def test_snapshot_accepts_old_schema_but_rejects_invalid_versions(self):
        self.assertTrue(valid_snapshot({"status": "published", "url": STORE_URL}))
        self.assertFalse(valid_snapshot({"status": "published", "url": STORE_URL, "version": "bad"}))

    def test_version_change_triggers_scheduled_deployment(self):
        previous = {"status": "published", "version": "2.0.16"}
        self.assertEqual(resolve(previous, "published", "schedule", True, "2.0.17"), ("published", True))
        self.assertEqual(resolve(previous, "published", "schedule", True, "2.0.16"), ("published", False))

    def test_network_failure_preserves_last_known_version(self):
        self.assertEqual(resolve({"status": "published", "version": "2.0.17"}, "unknown", "schedule", True), ("published", False))

    def test_missing_version_on_valid_listing_removes_stale_badge(self):
        self.assertEqual(resolve({"status": "published", "version": "2.0.17"}, "published", "schedule", True), ("published", True))

    def test_full_run_writes_extracted_version(self):
        baseline = {"status": "published", "url": STORE_URL, "version": "2.0.16"}
        html = PUBLISHED + '<section><h2>Details</h2><li><div>Version</div><div>2.0.17</div></li></section>'
        responses = [(200, STORE_URL, json.dumps(baseline)), (200, STORE_URL, html)]
        with TemporaryDirectory() as directory, patch("store_status.fetch", side_effect=responses), patch.dict("os.environ", {"GITHUB_OUTPUT": ""}), redirect_stdout(StringIO()):
            target = Path(directory) / "status.json"
            snapshot, deploy = run(target, "schedule")
            self.assertEqual(snapshot["version"], "2.0.17")
            self.assertTrue(deploy)

    def test_unavailable_listing_clears_version(self):
        baseline = {"status": "published", "url": STORE_URL, "version": "2.0.17"}
        responses = [(200, STORE_URL, json.dumps(baseline)), (404, STORE_URL, "")]
        with TemporaryDirectory() as directory, patch("store_status.fetch", side_effect=responses), patch.dict("os.environ", {"GITHUB_OUTPUT": ""}), redirect_stdout(StringIO()):
            snapshot, deploy = run(Path(directory) / "status.json", "schedule")
            self.assertEqual(snapshot["status"], "pending")
            self.assertIsNone(snapshot["version"])
            self.assertTrue(deploy)


if __name__ == "__main__":
    unittest.main()
