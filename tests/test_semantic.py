
from codex_repo_tool.semantic import build_index, find_symbol, dependency_graph
from pathlib import Path

def test_python_index(tmp_path: Path):
    p = tmp_path / "m.py"
    p.write_text("import os\nfrom sys import path\n\ndef foo(x):\n    return x\nclass C: pass\n", encoding="utf-8")
    idx = build_index(str(tmp_path))
    files = idx["files"]
    assert any("foo" == s["name"] for s in files[str(p)]["symbols"])
    deps = dependency_graph(idx)
    assert str(p) in deps

def test_js_index(tmp_path: Path):
    p = tmp_path / "m.js"
    p.write_text("import x from 'libx';\nconst a=1;\nfunction bar(){}\n", encoding="utf-8")
    idx = build_index(str(tmp_path))
    files = idx["files"]
    assert any("bar" == s["name"] for s in files[str(p)]["symbols"])
