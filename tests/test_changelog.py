"""
Tests for versioning and the changelog view.
"""
from pathlib import Path

from dogs_app import __version__
from dogs_app.utils.changelog import ChangelogEntry, load_changelog, parse_changelog

REPO_CHANGELOG = Path(__file__).parent.parent / 'CHANGELOG.md'


class TestParseChangelog:
    """Unit tests for the CHANGELOG.md parser."""

    def test_parses_entries_in_file_order(self):
        text = (
            '# Changelog\n\nIntro prose.\n\n'
            '## [2.0.2] - 2026-09-24\n- Second change\n\n'
            '## [2.0.1] - 2026-01-01\n- First change\n- Another\n'
        )
        assert parse_changelog(text) == [
            ChangelogEntry('2.0.2', '2026-09-24', ['Second change']),
            ChangelogEntry('2.0.1', '2026-01-01', ['First change', 'Another']),
        ]

    def test_heading_without_date(self):
        entries = parse_changelog('## [Unreleased]\n- Pending work\n')
        assert entries == [ChangelogEntry('Unreleased', None, ['Pending work'])]

    def test_entry_without_items(self):
        assert parse_changelog('## [1.0.0] - 2026-01-01\n') == [
            ChangelogEntry('1.0.0', '2026-01-01', [])
        ]

    def test_asterisk_bullets_and_continuation_lines(self):
        text = '## [1.0.0] - 2026-01-01\n* A long change\n  that wraps\n* Short\n'
        assert parse_changelog(text)[0].items == ['A long change that wraps', 'Short']

    def test_ignores_bullets_before_first_heading(self):
        assert parse_changelog('- stray\n## [1.0.0]\n- kept\n')[0].items == ['kept']

    def test_ignores_non_bullet_prose_inside_entry(self):
        text = '## [1.0.0] - 2026-01-01\nSome prose.\n- Real item\n'
        assert parse_changelog(text)[0].items == ['Real item']

    def test_ignores_other_heading_levels(self):
        text = '# Changelog\n### [9.9.9]\n## [1.0.0]\n- x\n'
        assert [e.version for e in parse_changelog(text)] == ['1.0.0']

    def test_windows_line_endings(self):
        text = '## [1.0.0] - 2026-01-01\r\n- Item\r\n'
        assert parse_changelog(text) == [ChangelogEntry('1.0.0', '2026-01-01', ['Item'])]

    def test_empty_text(self):
        assert parse_changelog('') == []

    def test_load_missing_file_returns_none(self, tmp_path):
        assert load_changelog(tmp_path / 'nope.md') is None

    def test_load_reads_utf8(self, tmp_path):
        path = tmp_path / 'CHANGELOG.md'
        path.write_text('## [1.0.0] - 2026-01-01\n- Café photos\n', encoding='utf-8')
        assert load_changelog(path)[0].items == ['Café photos']


class TestRepoChangelog:
    """Guard rails on the real CHANGELOG.md so the version can't drift."""

    def test_version_is_semver(self):
        parts = __version__.split('.')
        assert len(parts) == 3 and all(p.isdigit() for p in parts)

    def test_newest_entry_matches_version(self):
        entries = load_changelog(REPO_CHANGELOG)
        assert entries, 'CHANGELOG.md is missing or has no entries'
        assert entries[0].version == __version__

    def test_every_entry_has_date_and_items(self):
        for entry in load_changelog(REPO_CHANGELOG):
            assert entry.date, f'{entry.version} has no date'
            assert entry.items, f'{entry.version} has no items'

    def test_versions_are_unique(self):
        versions = [e.version for e in load_changelog(REPO_CHANGELOG)]
        assert len(versions) == len(set(versions))


class TestAboutRoutes:
    """Integration tests for the About page and changelog view."""

    def test_about_shows_version_linked_to_changelog(self, logged_in_viewer):
        response = logged_in_viewer.get('/about')
        assert response.status_code == 200
        html = response.data.decode()
        assert __version__ in html
        assert 'href="/about/changelog"' in html

    def test_changelog_requires_login(self, client):
        response = client.get('/about/changelog')
        assert response.status_code == 302
        assert '/login' in response.location

    def test_changelog_lists_entries_and_marks_current(self, logged_in_viewer):
        response = logged_in_viewer.get('/about/changelog')
        assert response.status_code == 200
        html = response.data.decode()
        for entry in load_changelog(REPO_CHANGELOG):
            assert entry.version in html
        assert 'changelog-current' in html

    def test_changelog_missing_file(self, app, logged_in_viewer, tmp_path):
        app.config['CHANGELOG_PATH'] = str(tmp_path / 'missing.md')
        response = logged_in_viewer.get('/about/changelog')
        assert response.status_code == 200
        assert b'not available' in response.data

    def test_changelog_with_no_entries(self, app, logged_in_viewer, tmp_path):
        path = tmp_path / 'CHANGELOG.md'
        path.write_text('# Changelog\n')
        app.config['CHANGELOG_PATH'] = str(path)
        response = logged_in_viewer.get('/about/changelog')
        assert b'No releases have been recorded yet' in response.data

    def test_changelog_escapes_html(self, app, logged_in_viewer, tmp_path):
        path = tmp_path / 'CHANGELOG.md'
        path.write_text('## [1.0.0] - 2026-01-01\n- <script>alert(1)</script>\n')
        app.config['CHANGELOG_PATH'] = str(path)
        response = logged_in_viewer.get('/about/changelog')
        assert b'<script>alert(1)</script>' not in response.data
        assert b'&lt;script&gt;' in response.data
