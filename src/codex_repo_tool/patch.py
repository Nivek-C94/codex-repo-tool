from __future__ import annotations
import json
import subprocess
import tempfile
from pathlib import Path
from dataclasses import dataclass
from .config import SETTINGS
from .qa import run_tests, lint_code
from .policy import load_policy
from .sandbox import with_worktree

@dataclass
class PatchMeta:
    id: str
    file: str
    description: str

def _ensure_patches_dir() -> Path:
    d = Path(SETTINGS.patches_dir)
    d.mkdir(parents=True, exist_ok=True)
    return d

def propose_patch(file: str, diff: str, description: str) -> str:
    """
    Store diff in patches dir; return patch id.
    Diff must be unified format generated vs current working tree.
    """
    patches_dir = _ensure_patches_dir()
    pid = f"patch_{abs(hash((file, diff, description))) & 0xFFFFFFFF:x}"
    meta = PatchMeta(id=pid, file=file, description=description)
    (patches_dir / f"{pid}.diff").write_text(diff, encoding="utf-8")
    (patches_dir / f"{pid}.json").write_text(json.dumps(meta.__dict__, indent=2), encoding="utf-8")
    return pid

def apply_patch(patch_id: str, run_lint: bool = True, run_test: bool = True) -> dict:
    patches_dir = _ensure_patches_dir()
    diff_path = patches_dir / f"{patch_id}.diff"
    if not diff_path.exists():
        raise FileNotFoundError(f"Patch not found: {patch_id}")

    # Dry-run apply to validate
    dry = subprocess.run(["git", "apply", "--check", str(diff_path)], capture_output=True, text=True)
    if dry.returncode != 0:
        return {"applied": False, "stage": "dry-run", "stdout": dry.stdout, "stderr": dry.stderr}

    # Actually apply
    apply = subprocess.run(["git", "apply", str(diff_path)], capture_output=True, text=True)
    if apply.returncode != 0:
        return {"applied": False, "stage": "apply", "stdout": apply.stdout, "stderr": apply.stderr}

    lint_ok = True
    tests_ok = True
    lint_log = ""
    test_log = ""

    if run_lint:
        lint_res = lint_code()
        lint_ok = lint_res.get("ok", True)
        lint_log = lint_res.get("stdout", "") + lint_res.get("stderr", "")

    if run_test and lint_ok:
        test_res = run_tests()
        tests_ok = test_res.get("ok", True)
        test_log = test_res.get("stdout", "") + test_res.get("stderr", "")

    if (run_lint and not lint_ok) or (run_test and not tests_ok):
        # rollback
        subprocess.run(["git", "reset", "--hard", "HEAD", "--"], capture_output=True)
        return {"applied": False, "stage": "checks", "lint_ok": lint_ok, "tests_ok": tests_ok,
                "lint_log": lint_log, "test_log": test_log}

    return {"applied": True, "stage": "done", "lint_ok": lint_ok, "tests_ok": tests_ok}

def discard_patch(patch_id: str) -> bool:
    patches_dir = _ensure_patches_dir()
    ok = False
    for ext in (".diff", ".json"):
        p = patches_dir / f"{patch_id}{ext}"
        if p.exists():
            p.unlink()
            ok = True
    return ok


def propose_bundle(items: list[dict], description: str = "") -> str:
    patches_dir = _ensure_patches_dir()
    bid = f"bundle_{abs(hash(tuple((i.get('file'), i.get('diff')) for i in items))) & 0xFFFFFFFF:x}"
    bundle = {"id": bid, "description": description, "items": items}
    (patches_dir / f"{bid}.json").write_text(json.dumps(bundle, indent=2), encoding="utf-8")
    return bid

def apply_bundle(bundle_id: str, branch: str | None = None) -> dict:
    patches_dir = _ensure_patches_dir()
    bpath = patches_dir / f"{bundle_id}.json"
    if not bpath.exists():
        raise FileNotFoundError(f"Bundle not found: {bundle_id}")
    bundle = json.loads(bpath.read_text(encoding="utf-8"))
    policy = load_policy(".")

    def _apply_in_wt(wt: str) -> dict:
        import subprocess
        from pathlib import Path as _P
        wt_path = _P(wt)
        for i, item in enumerate(bundle.get("items", []), start=1):
            f = item["file"]
            if policy.is_path_protected(f):
                return {"applied": False, "stage": "policy", "error": f"Protected path: {f}"}
            diff_file = wt_path / f".codexrt/tmp_{i}.diff"
            diff_file.parent.mkdir(parents=True, exist_ok=True)
            diff_file.write_text(item["diff"], encoding="utf-8")
            dry = subprocess.run(["git", "apply", "--check", str(diff_file)], cwd=wt, capture_output=True, text=True)
            if dry.returncode != 0:
                return {"applied": False, "stage": "dry-run", "stdout": dry.stdout, "stderr": dry.stderr}
            apply = subprocess.run(["git", "apply", str(diff_file)], cwd=wt, capture_output=True, text=True)
            if apply.returncode != 0:
                return {"applied": False, "stage": "apply", "stdout": apply.stdout, "stderr": apply.stderr}

        lint_ok = True
        tests_ok = True
        lint_log = ""
        test_log = ""

        if policy.require_checks.get("lint", True):
            from .qa import lint_code
            lintr = lint_code(None)
            lint_ok = lintr.get("ok", True)
            lint_log = (lintr.get("stdout", "") + lintr.get("stderr", ""))

        if policy.require_checks.get("tests", True) and lint_ok:
            from .qa import run_tests
            testr = run_tests(None)
            tests_ok = testr.get("ok", True)
            test_log = (testr.get("stdout", "") + testr.get("stderr", ""))

        if (policy.require_checks.get("lint", True) and not lint_ok) or            (policy.require_checks.get("tests", True) and not tests_ok):
            return {"applied": False, "stage": "checks", "lint_ok": lint_ok, "tests_ok": tests_ok,
                    "lint_log": lint_log, "test_log": test_log}

        return {"applied": True, "stage": "done", "lint_ok": lint_ok, "tests_ok": tests_ok}

    branch_or_head = branch or "HEAD"
    ok, data = with_worktree(branch_or_head, _apply_in_wt)
    if not ok:
        return {"applied": False, "stage": "sandbox", **data}
    return data
