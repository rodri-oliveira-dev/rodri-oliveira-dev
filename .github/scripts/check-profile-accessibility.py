"""Check selected editorial accessibility conventions, not WCAG conformance."""
from html.parser import HTMLParser
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
READMES = {
    "README.md": ("português", "pt"),
    "README.en.md": ("english", "en"),
    "README.es.md": ("español", "es"),
}


class Images(HTMLParser):
    def __init__(self):
        super().__init__()
        self.images = []
        self.sources = []

    def handle_starttag(self, tag, attrs):
        if tag == "img":
            self.images.append(dict(attrs))
        elif tag == "source":
            self.sources.append(dict(attrs))


def check(path, anchor, language):
    content = path.read_text(encoding="utf-8")
    errors = []
    parser = Images()
    parser.feed(content)
    for img in parser.images:
        if not (img.get("alt") or "").strip():
            errors.append("HTML image without a descriptive alt attribute")
    for alt in re.findall(r"!\[([^\]]*)\]\(", content):
        if not alt.strip():
            errors.append("Markdown image without alternative text")
    headings = [len(h) for h in re.findall(r"^(#{1,6})\s+", content, re.M)]
    if headings.count(1) != 1 or not headings or headings[0] != 1:
        errors.append("Expected one initial level-one heading")
    if any(b > a + 1 for a, b in zip(headings, headings[1:])):
        errors.append("Skipped heading level")
    if f"(ACCESSIBILITY.md#{anchor})" not in content:
        errors.append("Missing language-specific accessibility statement link")
    for suffix in (".png", ".mobile.png"):
        asset = f"assets/profile/software-architecture-in-practice.{language}{suffix}"
        if not (ROOT / asset).is_file() or asset not in content:
            errors.append(f"Missing infographic variant: {asset}")
    if not re.search(r"</picture>\s*</p>\s*\n\s*\*\*[^\n]+\*\*:", content):
        errors.append("Missing visible infographic description")
    return errors


def main():
    failed = False
    for filename, (anchor, language) in READMES.items():
        for error in check(ROOT / filename, anchor, language):
            print(f"{filename}: {error}", file=sys.stderr)
            failed = True
    if not failed:
        print("Profile accessibility conventions passed (not a WCAG audit).")
    return int(failed)


if __name__ == "__main__":
    sys.exit(main())
