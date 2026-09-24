# Comanche Dogs — Backlog

## Versioning bootstrap
- [x] Add CHANGELOG.md with baseline entry (2.0.1, plus 2.0.2 for this change)
- [x] Wire version into source (`dogs_app.__version__` is the single source of truth)
- [x] Keep version information where it currently is, but allow user to click on the version number to display the change log.

### Review
- Version moved from a constant in `routes/about.py` to `dogs_app/__init__.py`
- `/about/changelog` renders CHANGELOG.md via a small parser (`utils/changelog.py`), no Markdown dependency; handles missing/empty files and escapes content
- `tests/test_changelog.py` (21 tests) includes a guard that the newest changelog entry matches `__version__`
- Suite: 47 passed (was 26)
