"""Regenerate the policy body from the local, verbatim bilingual PRIVACY.md."""
from html import escape
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def articles():
    source = (ROOT / "PRIVACY.md").read_text(encoding="utf-8")
    sections = re.split(r"(?m)^# ", source)[1:]
    result = []
    for language, section in zip(("en", "ru"), sections, strict=True):
        blocks = re.split(r"\n\s*\n", section.strip())
        result.append(f'<article class="policy-article" lang="{language}" data-policy-language="{language}">')
        result.append(f'<h2 class="visually-hidden">{escape(blocks[0])}</h2>')
        heading = 0
        for index, block in enumerate(blocks[1:]):
            if block.startswith("## "):
                anchor = ("processing", "storage", "network", "changes")[heading]
                result.append(f'<h2 id="{language}-{anchor}">{escape(block[3:])}</h2>')
                heading += 1
            else:
                css = ' class="policy-meta"' if index == 0 else ""
                result.append(f'<p{css}>{escape(block)}</p>')
        result.append("</article>")
    return "\n".join(result)


if __name__ == "__main__":
    path = ROOT / "policy/index.html"
    template = path.read_text(encoding="utf-8")
    start, end = "<!-- policy:start -->", "<!-- policy:end -->"
    before, rest = template.split(start, 1)
    _, after = rest.split(end, 1)
    path.write_text(before + start + "\n" + articles() + "\n" + end + after, encoding="utf-8")
    print("Regenerated both policy languages from PRIVACY.md.")
