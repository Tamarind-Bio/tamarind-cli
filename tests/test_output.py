"""Tests for the plain-text table renderer — the fixes that keep `tamarind jobs`
(and every other table) readable regardless of cell content."""

from tamarind.cli.output import _cell, _truncate, render_table


def test_empty_rows():
    assert render_table([], ["a", "b"]) == "(none)"


def test_no_trailing_whitespace_even_with_a_giant_cell():
    # The bug: one huge Score cell padded every other row with ~900 trailing spaces.
    rows = [{"a": "x", "b": "y" * 900}, {"a": "short", "b": ""}]
    out = render_table(rows, ["a", "b"], max_width=100)
    for ln in out.splitlines():
        assert ln == ln.rstrip(), f"trailing whitespace: {ln!r}"


def test_table_fits_terminal_width():
    rows = [{"a": "x" * 100, "b": "y" * 100, "c": "z" * 100}]
    out = render_table(rows, ["a", "b", "c"], max_width=60)
    for ln in out.splitlines():
        assert len(ln) <= 60, (len(ln), ln)


def test_long_cell_is_truncated_with_ellipsis():
    out = render_table([{"a": "abcdefghij"}], ["a"], max_width=6)
    assert "…" in out


def test_giant_cell_fits_a_wide_but_finite_terminal():
    # A 900-char cell is shrunk to fit whatever terminal width is available.
    rows = [{"a": "z" * 900, "b": "ok"}]
    out = render_table(rows, ["a", "b"], max_width=200)
    assert max(len(ln) for ln in out.splitlines()) <= 200
    assert "…" in out  # and it's clipped with an ellipsis, not silently cut


def test_numeric_column_is_right_aligned():
    rows = [{"name": "protein", "tools": 263}, {"name": "cryoem", "tools": 6}]
    lines = render_table(rows, ["name", "tools"], max_width=80).splitlines()
    body1, body2 = lines[2], lines[3]
    # Right-aligned numeric column: both rows end at the same right edge.
    assert body1.endswith("263")
    assert body2.endswith("6") and not body2.endswith(" ")
    assert len(body1) == len(body2)


def test_text_column_stays_left_aligned():
    rows = [{"a": "x", "b": "hello"}, {"a": "y", "b": "hi"}]
    lines = render_table(rows, ["a", "b"], max_width=80).splitlines()
    # Non-numeric last column left-aligned → content starts right after the gap.
    assert lines[2].endswith("hello")
    assert lines[3].endswith("hi")  # no left-padding of a text column


def test_newlines_and_tabs_are_flattened():
    out = render_table([{"a": "line1\nline2\tend"}], ["a"], max_width=100)
    body = out.splitlines()[2:]  # skip header + separator
    assert len(body) == 1  # the embedded newline did NOT create a second row
    assert "line1 line2 end" in body[0]


def test_header_and_separator():
    lines = render_table([{"a": "1"}], ["a"]).splitlines()
    assert lines[0].startswith("a")
    assert set(lines[1]) == {"-"}  # separator is a dash rule


def test_cell_helper():
    assert _cell(None) == ""
    assert _cell("  a\n b ") == "a b"
    assert _cell(123) == "123"


def test_truncate_helper():
    assert _truncate("abcdef", 4) == "abc…"
    assert _truncate("ab", 5) == "ab"
    assert _truncate("abc", 0) == ""
    assert _truncate("abc", 1) == "…"
