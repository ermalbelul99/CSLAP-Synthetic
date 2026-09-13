"""Bounded, file-logged child execution; deliberately free of campaign logic."""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import time
import uuid

import psutil

from .protocol import ContractError, canonical_json


def _limits(deadline_seconds, memory_limit_bytes):
    for name, value in (("deadline_seconds", deadline_seconds), ("memory_limit_bytes", memory_limit_bytes)):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0 or value != value or value == float("inf"):
            raise ContractError("DATA_CONTRACT_ERROR", f"{name} must be finite and positive")


def _new(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    return path.open("xb")


def _publish(path, value):
    """Exclusive publication: a pre-existing/corrupt record is never replaced."""
    temporary = path.with_name(path.name + ".partial-" + uuid.uuid4().hex)
    with _new(temporary) as handle:
        handle.write(canonical_json(value).encode("utf-8"))
        handle.flush()
        os.fsync(handle.fileno())
    try:
        os.link(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _identity(pid):
    process = psutil.Process(pid)
    return {"pid": pid, "create_time": process.create_time()}


def _same(identity):
    try:
        return abs(psutil.Process(identity["pid"]).create_time() - identity["create_time"]) < .001
    except (psutil.NoSuchProcess, KeyError, TypeError):
        return False


def _tree(identity):
    if not _same(identity): return []
    try:
        root = psutil.Process(identity["pid"])
        return [root, *root.children(recursive=True)]
    except psutil.NoSuchProcess:
        return []


def _terminate(identity, tracked=()):
    """Kill only processes whose captured PID+creation time still agrees."""
    captured = {tuple(v.items()): v for v in tracked}
    if identity is not None:
        captured[tuple(identity.items())] = identity
        try:
            for p in _tree(identity):
                child = {"pid": p.pid, "create_time": p.create_time()}
                captured[tuple(child.items())] = child
        except psutil.Error:
            pass
    processes = []
    for child in captured.values():
        try:
            if _same(child):
                processes.append(psutil.Process(child["pid"]))
        except psutil.Error:
            pass
    for process in reversed(processes):
        try: process.terminate()
        except psutil.Error: pass
    _, alive = psutil.wait_procs(processes, timeout=1)
    for process in alive:
        try: process.kill()
        except psutil.Error: pass
    psutil.wait_procs(alive, timeout=1)


def execute(command, *, cwd, attempt_dir, deadline_seconds, memory_limit_bytes, popen=subprocess.Popen):
    """Run a claimed child with bounded wall/RSS usage and exclusive raw logs."""
    _limits(deadline_seconds, memory_limit_bytes)
    if not isinstance(command, list) or not command or any(not isinstance(v, str) for v in command):
        raise ContractError("DATA_CONTRACT_ERROR", "command must be a nonempty string list")
    started, directory = time.monotonic(), Path(attempt_dir)
    stdout_path, stderr_path, child_path = directory / "stdout.txt", directory / "stderr.txt", directory / "child.json"
    result = dict(status="LAUNCH_ERROR", returncode=None, pid=None, create_time=None, elapsed_seconds=0.0,
                  peak_rss_bytes=0, stdout_path=str(stdout_path), stderr_path=str(stderr_path), error=None)
    proc, identity, tracked = None, None, {}
    try:
        if child_path.exists():
            raise FileExistsError(str(child_path))
        with _new(stdout_path) as out, _new(stderr_path) as err:
            try:
                proc = popen(command, cwd=str(cwd), stdout=out, stderr=err, shell=False,
                             creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            except Exception as exc:
                result["error"] = f"{type(exc).__name__}: {exc}"
                return result
            try:
                identity = _identity(proc.pid)
            except psutil.NoSuchProcess:
                code = proc.poll()
                if code is None:
                    raise
                _publish(child_path, {"pid": proc.pid, "create_time": None, "already_exited": True})
                result.update(status="EXITED" if code == 0 else "PROCESS_ERROR", pid=proc.pid, returncode=code)
                return result
            _publish(child_path, identity)  # fsync + atomic publication before monitoring
            result.update(identity)
            while True:
                result["elapsed_seconds"] = time.monotonic() - started
                members = _tree(identity)
                rss = 0
                for p in members:
                    try:
                        child = {"pid": p.pid, "create_time": p.create_time()}
                        tracked[(p.pid, child["create_time"])] = child
                        rss += p.memory_info().rss
                    except psutil.NoSuchProcess:
                        continue
                result["peak_rss_bytes"] = max(result["peak_rss_bytes"], rss)
                code = proc.poll()
                if result["elapsed_seconds"] >= deadline_seconds:
                    _terminate(identity, tracked.values())
                    result.update(status="TIMEOUT", error="deadline exceeded", returncode=proc.poll())
                    return result
                if rss > memory_limit_bytes:
                    _terminate(identity, tracked.values())
                    result.update(status="MEMORY_LIMIT", error="RSS limit exceeded", returncode=proc.poll())
                    return result
                if code is not None:
                    result.update(status="EXITED" if code == 0 else "PROCESS_ERROR", returncode=code)
                    return result
                time.sleep(min(.05, max(0, deadline_seconds - result["elapsed_seconds"])))
    except FileExistsError:
        result.update(status="PROCESS_ERROR", error="attempt log or child identity already exists")
    except Exception as exc:
        result.update(status="PROCESS_ERROR", error=f"{type(exc).__name__}: {exc}")
    finally:
        if proc is not None:
            try:
                if proc.poll() is None:
                    _terminate(identity, tracked.values())
                    # Popen owns the native process handle on Windows, so this
                    # remains safe when psutil identity capture itself failed.
                    if proc.poll() is None:
                        proc.kill()
                    proc.wait(timeout=2)
            except (OSError, subprocess.TimeoutExpired, psutil.Error) as exc:
                result["cleanup_error"] = f"{type(exc).__name__}: {exc}"
        result["elapsed_seconds"] = time.monotonic() - started
    return result
