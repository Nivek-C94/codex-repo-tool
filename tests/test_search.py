from codex_repo_tool.search import search_code
from pathlib import Path

def test_search(tmp_path: Path):
    f = tmp_path / "a.py"
    f.write_text("def add(a,b):\n    return a+b\n", encoding="utf-8")
    res = search_code("add", root=str(tmp_path))
    assert any(r["line"] == 1 for r in res)
