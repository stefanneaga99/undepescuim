import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

import rebuild_data


def test_scratch_rebuild_copies_locality_inputs():
    assert "data/raw/localities" in rebuild_data.SCRATCH_COPY_DIRS
    for rel in rebuild_data.SCRATCH_COPY_DIRS:
        assert (Path(rebuild_data.ROOT) / rel).is_dir(), rel


def _patch_scratch_rebuild(monkeypatch, steps, exit_codes):
    """Run cmd_to against fake steps: no copying, no hashing, no real scripts."""
    calls = []
    monkeypatch.setattr(rebuild_data, "SCRATCH_COPY_DIRS", [])
    monkeypatch.setattr(rebuild_data, "OUTPUTS", [])
    monkeypatch.setattr(rebuild_data, "FULL_STEPS", steps)

    def fake_run(cmd, cwd=None, **kwargs):
        step = Path(cmd[1]).relative_to(cwd).as_posix()
        calls.append(step)
        return SimpleNamespace(returncode=exit_codes.get(step, 0))

    monkeypatch.setattr(rebuild_data.subprocess, "run", fake_run)
    return calls


STEPS = ["scripts/a.py", "scripts/b.py", "scripts/c.py"]


def test_to_aborts_on_first_failing_step(tmp_path, monkeypatch):
    calls = _patch_scratch_rebuild(monkeypatch, STEPS, {"scripts/b.py": 2})
    with pytest.raises(SystemExit) as excinfo:
        rebuild_data.cmd_to(tmp_path / "scratch")
    assert excinfo.value.code == 1
    assert calls == ["scripts/a.py", "scripts/b.py"]  # c.py never ran


def test_to_succeeds_when_every_step_passes(tmp_path, monkeypatch):
    calls = _patch_scratch_rebuild(monkeypatch, STEPS, {})
    rebuild_data.cmd_to(tmp_path / "scratch")  # must not raise SystemExit
    assert calls == STEPS


def test_to_keep_going_runs_every_step_and_does_not_exit(tmp_path, monkeypatch):
    calls = _patch_scratch_rebuild(monkeypatch, STEPS, {"scripts/a.py": 1, "scripts/c.py": 3})
    rebuild_data.cmd_to(tmp_path / "scratch", keep_going=True)
    assert calls == STEPS


def test_run_steps_reports_failures(tmp_path, monkeypatch):
    codes = {"scripts/b.py": 2, "scripts/c.py": 1}
    _patch_scratch_rebuild(monkeypatch, STEPS, codes)
    assert rebuild_data.run_steps(tmp_path) == ["scripts/b.py"]  # fail-fast stops at b
    assert rebuild_data.run_steps(tmp_path, keep_going=True) == ["scripts/b.py", "scripts/c.py"]


def test_cli_passes_keep_going_flag(tmp_path, monkeypatch):
    seen = {}
    monkeypatch.setattr(rebuild_data, "cmd_to", lambda dest, keep_going=False: seen.update(dest=dest, keep_going=keep_going))
    monkeypatch.setattr(sys, "argv", ["rebuild_data.py", "--to", str(tmp_path / "d")])
    rebuild_data.main()
    assert seen == {"dest": tmp_path / "d", "keep_going": False}
    monkeypatch.setattr(sys, "argv", ["rebuild_data.py", "--to", str(tmp_path / "d"), "--keep-going"])
    rebuild_data.main()
    assert seen["keep_going"] is True


def test_rivernet_publish_runs_right_after_the_merge_and_its_inputs_exist():
    steps = rebuild_data.FULL_STEPS
    assert steps.index("scripts/rivernet_publish.py") == steps.index("scripts/merge_anpa_waters.py") + 1
    assert steps.index("scripts/rivernet_publish.py") < steps.index("scripts/build_locality_assignment.py")
    for rel in rebuild_data.RIVERNET_INPUTS:  # pinned into INPUTS at the cutover (T4.4)
        assert (rebuild_data.ROOT / rel).exists()
    assert {"data/rivernet", "data/sectors"} <= set(rebuild_data.SCRATCH_COPY_DIRS)
    assert (rebuild_data.ROOT / "scripts/rivernet_publish.py").exists()


def test_rivernet_publish_shim_writes_from_the_committed_inputs(monkeypatch):
    import importlib.util

    spec = importlib.util.spec_from_file_location("rivernet_publish_shim", rebuild_data.ROOT / "scripts/rivernet_publish.py")
    shim = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(shim)
    seen = {}
    monkeypatch.setattr(shim, "cli", lambda argv: seen.setdefault("argv", argv) and 0)
    assert shim.main() == 0
    argv = seen["argv"]
    assert argv[:2] == ["--mode", "write"]
    assert argv[argv.index("--waters") + 1].replace("\\", "/").endswith("public/data/waters.json")
    assert argv[argv.index("--sectors") + 1].replace("\\", "/").endswith("data/sectors/sectors.jsonl")
