"""Check static pages, local references, policy completeness, and publish inputs."""
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import struct
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]
PREFIX = "/md-it/"


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.refs = []
        self.ids = []
        self.images = []
        self.translations = 0

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        for key in ("href", "src"):
            if key in attrs:
                self.refs.append(attrs[key])
        if tag == "img":
            self.images.append(attrs)
        if "data-ru" in attrs:
            assert "data-en" in attrs, "Missing English translation"
            self.translations += 1


def check():
    for relative in ("index.html", "policy/index.html"):
        page = Page()
        content = (ROOT / relative).read_text(encoding="utf-8")
        page.feed(content)
        assert len(page.ids) == len(set(page.ids)), f"Duplicate IDs: {relative}"
        assert '<html lang="ru">' in content
        for meta in ('name="description"', 'property="og:title"', 'property="og:image"', 'rel="canonical"'):
            assert meta in content, f"Missing metadata: {relative}: {meta}"
        for image in page.images:
            assert "alt" in image and "width" in image and "height" in image
        for ref in page.refs:
            url = urlsplit(ref)
            if url.scheme or url.netloc:
                continue
            if not url.path:
                assert not url.fragment or unquote(url.fragment) in page.ids, f"Broken fragment {ref}"
                continue
            assert url.path.startswith(PREFIX), f"Incorrect base path: {ref}"
            target = ROOT / url.path[len(PREFIX):]
            if target.is_dir():
                target /= "index.html"
            assert target.is_file(), f"Missing local resource: {target}"
        assert not re.search(r"[A-Z]:[\\/]|localhost|127\.0\.0\.1", content), "Local path in public HTML"
        print(f"PASS {relative}: {len(page.ids)} IDs, {len(page.refs)} references, {page.translations} translations")
    policy = (ROOT / "policy/index.html").read_text(encoding="utf-8")
    source = (ROOT / "PRIVACY.md").read_text(encoding="utf-8")
    class Text(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.parts = []
        def handle_data(self, data):
            self.parts.append(data)
    plain = Text()
    plain.feed(policy)
    text = re.sub(r"\s+", " ", " ".join(plain.parts))
    for paragraph in re.split(r"\n\s*\n", source.strip()):
        normalized = re.sub(r"\s+", " ", re.sub(r"^#+ ", "", paragraph)).strip()
        assert normalized in text, f"Policy paragraph missing or changed: {normalized[:100]}"
    print("PASS policy: both language versions match every paragraph in PRIVACY.md")
    for locale in ("en", "ru"):
        for shot in ("panel", "picker", "preview", "options"):
            data = (ROOT / f"assets/screenshots/{locale}/{shot}.png").read_bytes()
            assert data[:8] == b"\x89PNG\r\n\x1a\n"
            assert struct.unpack(">II", data[16:24]) == (1280, 800)
    icon = (ROOT / "assets/icon.png").read_bytes()
    assert icon[25] == 6, "Icon must preserve its RGBA channel"
    print("PASS assets: 8 original 1280x800 screenshots and RGBA PNG icon")
    for file in ("assets/site.css", "assets/site.js", "assets/store-status.json", ".nojekyll", "robots.txt", "sitemap.xml"):
        assert (ROOT / file).is_file(), f"Missing publish input: {file}"
    status = json.loads((ROOT / "assets/store-status.json").read_text(encoding="utf-8"))
    assert status["status"] in ("pending", "published")
    assert status["url"] == "https://chromewebstore.google.com/detail/pbajjhnmfaopgjblomoecaaokihjajli"
    assert "prefers-reduced-motion" in (ROOT / "assets/site.css").read_text(encoding="utf-8")
    print("All static checks passed.")


if __name__ == "__main__":
    check()
