import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import threading


def load_parent_watchdog():
    module_path = Path(__file__).resolve().parents[1] / "mlx_lm" / "_parent_watchdog.py"
    spec = importlib.util.spec_from_file_location("parent_watchdog_test", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_parent_is_alive_current_process():
    watchdog = load_parent_watchdog()

    assert watchdog.parent_is_alive(os.getpid()) is True


def test_parent_is_alive_dead_pid():
    watchdog = load_parent_watchdog()
    proc = subprocess.Popen([sys.executable, "-c", "pass"])
    proc.wait(timeout=5)

    assert watchdog.parent_is_alive(proc.pid) is False


def test_parent_is_alive_permission_error(monkeypatch):
    watchdog = load_parent_watchdog()

    def raise_permission_error(pid, signal):
        raise PermissionError

    monkeypatch.setattr(watchdog.os, "kill", raise_permission_error)

    assert watchdog.parent_is_alive(12345) is True


def test_parent_watchdog_exits_when_parent_dies():
    watchdog = load_parent_watchdog()
    proc = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
    event = threading.Event()
    exit_code = {}

    def fake_exit(code):
        exit_code["code"] = code
        event.set()

    try:
        watchdog.start_parent_watchdog(proc.pid, poll_interval=0.05, _exit=fake_exit)
        assert event.wait(0.2) is False

        proc.kill()
        proc.wait(timeout=5)

        assert event.wait(2.0) is True
        assert exit_code["code"] == 0
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=5)
