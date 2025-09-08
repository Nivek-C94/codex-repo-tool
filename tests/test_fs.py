from pathlib import Path

from codex_repo_tool.fs_utils import list_files, read_file


def test_list_and_read(tmp_path: Path):
    d = tmp_path / "pkg"
    d.mkdir()
    f = d / "x.txt"
    f.write_text("hello\nworld\n", encoding="utf-8")
    files = list_files(str(tmp_path))
    assert any("x.txt" in x["path"] for x in files)
    assert read_file(str(f)) == "hello\nworld\n"
    assert read_file(str(f), (2, 2)) == "world"
