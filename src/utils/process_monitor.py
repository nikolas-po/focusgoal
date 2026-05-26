"""Мониторинг и блокировка процессов (ТЗ FR-009)"""
import os
import sys
import subprocess
from pathlib import Path
from typing import List, Dict, Callable, Optional
import psutil
import time


def _run_py() -> str:
    return str(Path(__file__).resolve().parent.parent.parent / "run.py")


class ProcessMonitor:
    def __init__(self):
        self._blocked: Dict[str, int] = {}
        self._warning_callback: Optional[Callable] = None

    def set_blocked_processes(self, names: List[str]):
        self._blocked = {n.lower(): 1 for n in names if n}

    def set_blocked_apps(self, apps: Dict[str, int]):
        self._blocked = {k.lower(): int(v) for k, v in apps.items() if k}

    def set_warning_callback(self, cb: Callable):
        self._warning_callback = cb

    def get_running_processes(self) -> List[Dict]:
        result = []
        for p in psutil.process_iter(["pid", "name", "exe"]):
            try:
                result.append({"pid": p.info["pid"], "name": p.info["name"],
                               "exe": p.info.get("exe") or ""})
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return result

    def check_blocked_running(self) -> List[Dict]:
        return [
            {**p, "block_level_id": self._blocked.get(p["name"].lower(), 2)}
            for p in self.get_running_processes()
            if p["name"] and p["name"].lower() in self._blocked
        ]

    def terminate_process(self, pid: int, force: bool = False) -> bool:
        try:
            proc = psutil.Process(pid)
            proc.kill() if force else proc.terminate()
            return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, PermissionError):
            return False

    def check_admin_rights(self) -> bool:
        # Linux: проверка root
        return os.geteuid() == 0

    def request_admin_rights(self, launch_args: list = None) -> bool:
        """Перезапустить с правами root через pkexec."""
        if not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
            return False

        try:
            run_py = _run_py()
            extra = [f"--close-pid={os.getpid()}"] + (launch_args or [])
            cmd = ["pkexec", "env"]
            for k in ("DISPLAY", "XAUTHORITY", "WAYLAND_DISPLAY", "QT_QPA_PLATFORM",
                      "XDG_RUNTIME_DIR", "HOME"):
                if os.environ.get(k):
                    cmd.append(f"{k}={os.environ[k]}")
            cmd += [sys.executable, run_py] + extra
            try:
                subprocess.Popen(cmd)
            except Exception:
                return False

            deadline = time.time() + 5.0
            close_arg = f"--close-pid={os.getpid()}"
            while time.time() < deadline:
                try:
                    for pr in psutil.process_iter(attrs=['pid', 'name', 'cmdline']):
                        try:
                            cmdline = pr.info.get('cmdline') or []
                            # Проверяем, что в командной строке присутствует наш run.py
                            # и передан аргумент --close-pid (тот же PID), и процесс запущен от root.
                            if any(str(run_py) in str(c) or 'run.py' in str(c) for c in cmdline) and any(close_arg in str(c) for c in cmdline):
                                try:
                                    # Некоторые процессы могут не позволять читать uid; игнорируем в таком случае
                                    if pr.uids().effective == 0:
                                        return True
                                except Exception:
                                    pass
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            continue
                except Exception:
                    pass
                time.sleep(0.2)
            return False
        except Exception:
            return False