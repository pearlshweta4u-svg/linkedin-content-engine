"""Git is the database's durability layer: every state change is committed and
pushed before the next irreversible step, so a crashed or restarted run (or a
second run) sees it."""
from __future__ import annotations

import subprocess
import time

from .config import ROOT


class GitSyncError(Exception):
    pass


def _git(*args: str) -> str:
    r = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0:
        raise GitSyncError(f"git {' '.join(args)} failed: {r.stderr.strip()[:500]}")
    return r.stdout.strip()


def current_branch() -> str:
    return _git("rev-parse", "--abbrev-ref", "HEAD")


def pull() -> None:
    b = current_branch()
    _git("fetch", "origin", b)
    _git("rebase", f"origin/{b}")


def commit_and_push(message: str, paths: list[str], retries: int = 4) -> None:
    """Commit the given paths and push. Raises GitSyncError if the push can't land;
    callers treat that as 'state not durable' and must not proceed."""
    _git("add", *paths)
    if not _git("status", "--porcelain", *paths):
        return
    _git("commit", "-m", message)
    b = current_branch()
    delay = 2
    for attempt in range(retries + 1):
        try:
            _git("push", "-u", "origin", b)
            return
        except GitSyncError:
            if attempt == retries:
                raise
            time.sleep(delay)
            delay *= 2
            # Someone else pushed: rebase onto it and retry.
            try:
                _git("pull", "--rebase", "origin", b)
            except GitSyncError:
                pass
