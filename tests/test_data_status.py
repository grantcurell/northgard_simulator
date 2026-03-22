from northgard.data_status import format_markdown_report


def test_markdown_report_structure():
    md = format_markdown_report()
    assert md.startswith("# Northgard simulator")
    assert "## 1. Sourced in the simulator" in md
    assert "## 1a. Partial public facts" in md
    assert "## 2. Unknown / not publicly sourced" in md
    assert "| `S1` |" in md
    assert "[DATA_GAPS.md](DATA_GAPS.md)" in md
