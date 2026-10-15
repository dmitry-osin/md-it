"""Check the public Web Store listing; deploy scheduled runs only when status changes."""
import argparse
from datetime import datetime, timezone
from html.parser import HTMLParser
import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

EXTENSION_ID = "pbajjhnmfaopgjblomoecaaokihjajli"
STORE_URL = f"https://chromewebstore.google.com/detail/{EXTENSION_ID}"
STATUS_URL = "https://dmitry-osin.github.io/md-it/assets/store-status.json"
ROOT = Path(__file__).resolve().parents[1]


class Listing(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.metadata = {}
        self.title = []
        self.text = []
        self.in_title = False
        self.ignored = 0

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if tag == "meta":
            self.metadata[attrs.get("property", attrs.get("name", ""))] = attrs.get("content", "")
        if tag == "title":
            self.in_title = True
        if tag in ("script", "style"):
            self.ignored += 1

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        if tag in ("script", "style"):
            self.ignored = max(0, self.ignored - 1)

    def handle_data(self, data):
        if self.in_title:
            self.title.append(data)
        if not self.ignored:
            self.text.append(data)


def classify(code, final_url, html, extension_id=EXTENSION_ID):
    """Require positive listing evidence; an HTTP 200 alone also covers unavailable items."""
    url = urlsplit(final_url)
    if url.hostname != "chromewebstore.google.com":
        return "unknown"
    if code in (404, 410) or url.path.endswith("/error"):
        return "pending"
    if code != 200:
        return "unknown"
    page = Listing()
    page.feed(html)
    text = " ".join(page.text).casefold()
    if "item not available" in text:
        return "pending"
    item_url = urlsplit(page.metadata.get("og:url", ""))
    expected_item = item_url.hostname == url.hostname and item_url.path.rstrip("/").endswith(f"/{extension_id}")
    if expected_item and page.metadata.get("description") and "add to chrome" in text:
        return "published"
    # The store serves this generic HTTP 200 page for an unpublished listing.
    if f"/detail/empty-title/{extension_id}" in url.path and " ".join(page.title).strip() == "Chrome Web Store":
        return "pending"
    return "unknown"


def fetch(url):
    request = Request(url, headers={
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "no-cache",
    })
    try:
        with urlopen(request, timeout=20) as response:
            content = response.read(4_000_001)
            if len(content) > 4_000_000:
                raise ValueError("Unexpectedly large store response")
            return response.status, response.url, content.decode("utf-8", errors="replace")
    except HTTPError as error:
        return error.code, error.url, ""


def valid_snapshot(value):
    return isinstance(value, dict) and value.get("status") in ("pending", "published") and value.get("url") == STORE_URL


def resolve(previous, observed, event, baseline_available):
    """A timeout or changed store markup must never hide an already confirmed release."""
    status = previous["status"] if observed == "unknown" else observed
    changed = status != previous["status"]
    deploy = event != "schedule" or (baseline_available and changed)
    return status, deploy


def run(output, event):
    previous = json.loads((ROOT / "assets/store-status.json").read_text(encoding="utf-8"))
    if not valid_snapshot(previous):
        raise ValueError("Invalid local store-status.json")
    baseline_available = False
    try:
        code, _, body = fetch(STATUS_URL)
        baseline = json.loads(body) if code == 200 else None
        if valid_snapshot(baseline):
            previous = baseline
            baseline_available = True
    except (OSError, ValueError, URLError):
        pass
    try:
        observed = classify(*fetch(STORE_URL + "?hl=en"))
    except (OSError, ValueError, URLError):
        observed = "unknown"
    if observed == "unknown":
        print("::warning::Could not confirm store availability; keeping the last known status.")
    if event == "schedule" and not baseline_available:
        print("::warning::Published status snapshot unavailable; skipping this scheduled deployment.")
    status, deploy = resolve(previous, observed, event, baseline_available)
    snapshot = {
        "status": status,
        "url": STORE_URL,
        "checkedAt": datetime.now(timezone.utc).isoformat() if observed != "unknown" else previous.get("checkedAt"),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as stream:
            stream.write(f"deploy={str(deploy).lower()}\n")
    print(f"Store: {observed}; effective status: {status}; deploy: {str(deploy).lower()}")
    return snapshot, deploy


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "_site/assets/store-status.json")
    parser.add_argument("--event", default=os.environ.get("GITHUB_EVENT_NAME", "manual"))
    args = parser.parse_args()
    run(args.output, args.event)
