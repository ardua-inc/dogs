"""
CHANGELOG.md parsing for the About page.

Understands the project's changelog format:

    ## [2.0.2] - 2026-09-24
    - One-line summary of what changed
      (indented lines continue the previous bullet)

Anything else (the title, intro prose, blank lines) is ignored, so the file
stays readable on GitHub without the parser needing a Markdown dependency.
"""
import re
from dataclasses import dataclass, field
from pathlib import Path

HEADING_RE = re.compile(r'^##\s+\[(?P<version>[^\]]+)\](?:\s*-\s*(?P<date>\S.*?))?\s*$')
BULLET_RE = re.compile(r'^[-*]\s+(?P<text>.+?)\s*$')


@dataclass
class ChangelogEntry:
    """One released version and its list of changes."""
    version: str
    date: str | None = None
    items: list[str] = field(default_factory=list)


def parse_changelog(text):
    """Parse changelog text into entries, newest first (file order)."""
    entries = []
    current = None

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        heading = HEADING_RE.match(line)
        if heading:
            current = ChangelogEntry(version=heading['version'].strip(),
                                     date=heading['date'])
            entries.append(current)
            continue

        if current is None or not line.strip():
            continue

        bullet = BULLET_RE.match(line)
        if bullet:
            current.items.append(bullet['text'])
        elif line[0].isspace() and current.items:
            # Indented continuation of a wrapped bullet
            current.items[-1] += ' ' + line.strip()

    return entries


def load_changelog(path):
    """Read and parse the changelog file; returns None if it can't be read."""
    try:
        text = Path(path).read_text(encoding='utf-8')
    except OSError:
        return None
    return parse_changelog(text)
