"""Check static pages, local references, policy completeness, and publish inputs."""
from html.parser import HTMLParser
from hashlib import sha256
import json
from pathlib import Path
import re
import struct
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]
PREFIX = "/md-it/"
SHOTS = ("panel", "picker", "preview", "tables", "options")


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.refs = []
        self.ids = []
        self.images = []
        self.translations = 0
        self.tags = []
        self.panels = {}
        self.panel = None

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        self.tags.append((tag, attrs))
        if tag == "figure" and "demo-panel" in attrs.get("class", "").split():
            self.panel = attrs["id"]
            self.panels[self.panel] = []
        if self.panel:
            self.panels[self.panel].append((tag, attrs))
        if "id" in attrs:
            self.ids.append(attrs["id"])
        for key in ("href", "src"):
            if key in attrs:
                self.refs.append(attrs[key])
        if tag == "img":
            self.images.append(attrs)
        if "data-ru" in attrs:
            assert "data-en" in attrs, "Missing English translation"
            assert attrs["data-ru"] and attrs["data-en"], "Empty translation"
            self.translations += 1

    def handle_endtag(self, tag):
        if tag == "figure":
            self.panel = None


def check_gallery(page):
    tabs = [attrs for tag, attrs in page.tags if "data-demo" in attrs]
    assert tuple(tab["data-demo"] for tab in tabs) == SHOTS, "Incorrect gallery tab order"
    assert tuple(page.panels) == tuple(f"demo-{shot}" for shot in SHOTS)
    labels = (("Панель", "Panel"), ("Выбор элемента", "Element Picker"),
              ("Предпросмотр", "Preview"), ("Таблицы", "Tables"), ("Настройки", "Settings"))
    for shot, tab, (ru, en) in zip(SHOTS, tabs, labels, strict=True):
        assert tab["id"] == f"tab-{shot}" and tab["aria-controls"] == f"demo-{shot}"
        panel = page.panels[f"demo-{shot}"]
        figure = panel[0][1]
        assert figure["aria-labelledby"] == tab["id"] and "hidden" not in figure
        image, = [attrs for tag, attrs in panel if tag == "img"]
        assert image["data-shot"] == shot
        assert image["src"] == f"{PREFIX}assets/screenshots/ru/{shot}.png"
        assert (image["width"], image["height"]) == ("1280", "800")
        assert image["alt"] == image["data-alt-ru"] and image["data-alt-en"]
        links = [attrs for tag, attrs in panel if "data-shot-link" in attrs]
        assert len(links) == 2, f"Missing full-size links: {shot}"
        for link in links:
            assert link["data-shot-link"] == shot and link["href"] == image["src"]
            assert link["target"] == "_blank" and "noopener" in link["rel"]
        assert any(tag == "figcaption" for tag, attrs in panel)
        assert len([attrs for tag, attrs in panel if "data-ru" in attrs]) == 3
        assert any(attrs.get("data-ru") == ru and attrs.get("data-en") == en
                   for tag, attrs in page.tags if tag == "span"), f"Missing tab translations: {shot}"
    print("PASS gallery: five ordered tabs, localized images/captions/alt, full-size links, no-JS figures")


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
        if relative == "index.html":
            check_gallery(page)
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
    text = re.sub(r"\s+", " ", "".join(plain.parts))
    for paragraph in re.split(r"\n\s*\n", source.strip()):
        normalized = re.sub(r"\s+", " ", re.sub(r"^#+ ", "", paragraph)).strip()
        assert normalized in text, f"Policy paragraph missing or changed: {normalized[:100]}"
    print("PASS policy: both language versions match every paragraph in PRIVACY.md")
    for locale in ("en", "ru"):
        manifest = json.loads((ROOT / f"scripts/screenshot-manifests/{locale}.json").read_text(encoding="utf-8"))
        assert manifest["locale"] == {"en": "en-US", "ru": "ru-RU"}[locale]
        assert tuple(file["name"] for file in manifest["files"]) == SHOTS
        assert {file.stem for file in (ROOT / f"assets/screenshots/{locale}").glob("*.png")} == set(SHOTS)
        for shot, original in zip(SHOTS, manifest["files"], strict=True):
            data = (ROOT / f"assets/screenshots/{locale}/{shot}.png").read_bytes()
            assert data[:8] == b"\x89PNG\r\n\x1a\n"
            assert struct.unpack(">II", data[16:24]) == (1280, 800)
            assert (original["width"], original["height"]) == (1280, 800)
            assert sha256(data).hexdigest() == original["sha256"], f"Changed original: {locale}/{shot}"
    icon = (ROOT / "assets/icon.png").read_bytes()
    assert icon[25] == 6, "Icon must preserve its RGBA channel"
    print("PASS assets: 10 original 1280x800 screenshots (SHA-256 verified) and RGBA PNG icon")
    for file in ("assets/site.css", "assets/site.js", "assets/store-status.json", ".nojekyll", "robots.txt", "sitemap.xml"):
        assert (ROOT / file).is_file(), f"Missing publish input: {file}"
    status = json.loads((ROOT / "assets/store-status.json").read_text(encoding="utf-8"))
    assert status["status"] in ("pending", "published")
    from store_status import valid_snapshot
    assert valid_snapshot(status), "Invalid store availability/version snapshot"
    assert status["url"] == "https://chromewebstore.google.com/detail/pbajjhnmfaopgjblomoecaaokihjajli"
    assert "prefers-reduced-motion" in (ROOT / "assets/site.css").read_text(encoding="utf-8")
    print("All static checks passed.")


if __name__ == "__main__":
    check()
