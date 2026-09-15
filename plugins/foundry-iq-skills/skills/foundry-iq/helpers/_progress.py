"""Bounded, content-free observations; never a service execution controller."""
from __future__ import annotations

from functools import wraps
import json
import math
import os
import sys
import time

try:
    from ._common import HelperFailure
except ImportError:
    from _common import HelperFailure


STAGES = {
    "file-source": ("validation", "source-reconciliation", "file-inventory", "file-upload", "file-readback"),
    "file-upload": ("file-inventory", "file-upload", "file-readback"),
    "blob-source": ("validation", "blob-inventory", "source-reconciliation", "ingestion-cycle",
                    "blob-readback", "source-readback"),
    "blob-monitor": ("ingestion-cycle",),
    "blob-capture": ("evidence-validation", "context-check", "source-binding", "blob-inventory", "checkpoint"),
    "blob-recheck": ("evidence-validation", "context-check", "source-binding", "blob-inventory",
                     "ingestion-cycle", "blob-readback", "source-readback", "context-readback"),
    "search-bootstrap": ("validation", "context-check", "region-check", "absence-check", "search-submit",
                         "arm-wait", "arm-readback"),
}
COUNTS = frozenset(("uploads_acknowledged", "files_reused", "files_verified",
                    "status_checks", "cycle_updates_processed", "cycle_items_skipped"))
IO_WARNING = "progress-output-failed: stderr progress could not be written; execution result is authoritative."
SHUTDOWN_WARNING = "progress-shutdown-flush-unresolved: failed stderr could not be redirected; shutdown may override the exit code."


class Progress:
    def __init__(self, workflow, *, enabled=True, stream=None, clock=time.monotonic):
        self.stages = STAGES[workflow]
        self.workflow = workflow
        self.enabled = enabled
        self.stream = stream
        self.clock = clock
        self.depth = 0
        self.stage = self.stages[0]
        self.counts = {}
        self.started = None
        self.elapsed = 0.0
        self.last_sent = None
        self.last_stage = None
        self.output_failed = False
        self.shutdown_flush_unresolved = False

    def update(self, stage, **counts):
        if stage not in self.stages or self.stages.index(stage) < self.stages.index(self.stage):
            raise ValueError("Invalid progress stage transition.")
        if any(key not in COUNTS or type(value) is not int or value < 0 for key, value in counts.items()):
            raise ValueError("Invalid progress count.")
        self.stage = stage
        self.counts.update(counts)
        self._emit("running")

    def _emit(self, state):
        if not self.enabled or self.output_failed:
            return
        observed = self.clock()
        # Clock regressions/nonfinite observations must not create negative time
        # or bypass throttling. Progress never shares the service deadline clock.
        if math.isfinite(observed):
            if self.started is None:
                self.started = observed
            delta = observed - self.started
            if math.isfinite(delta):
                self.elapsed = max(self.elapsed, delta)
        if (state == "running" and self.stage == self.last_stage
                and self.last_sent is not None and self.elapsed - self.last_sent < 1.0):
            return
        event = {
            "event": "progress", "workflow": self.workflow, "activity": self.stage,
            "state": state, "elapsed_seconds": round(self.elapsed, 3),
            "remaining_checks": [] if state == "completed" else list(self.stages[self.stages.index(self.stage) + 1:]),
        }
        if self.counts:
            event["completed_counts"] = dict(self.counts)
        stream = self.stream if self.stream is not None else sys.stderr
        try:
            text = json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n"
            if stream.write(text) != len(text):
                raise OSError("Short progress write.")
            stream.flush()
        except (OSError, UnicodeError, ValueError):
            # Continue the approved operation, retaining a fixed secondary warning
            # even when stderr itself is broken. Never replace a primary failure.
            self.output_failed = True
            self._disable_failed_default_stderr(stream)
        self.last_sent, self.last_stage = self.elapsed, self.stage

    def _disable_failed_default_stderr(self, stream):
        if self.stream is not None or stream is not sys.__stderr__ or stream.closed:
            return
        try:
            if stream.fileno() == 2:
                # A failed TextIOWrapper flush can retain pending bytes. Redirect
                # only the failed native stderr so shutdown can drain that buffer
                # without replacing the authoritative process exit status.
                sink = os.open(os.devnull, os.O_WRONLY)
                try:
                    os.dup2(sink, 2)
                finally:
                    if sink != 2:
                        os.close(sink)
        except (OSError, ValueError):
            self.shutdown_flush_unresolved = True

    def finish(self, result=None, failure=None):
        if failure is not None:
            state = "partial" if failure.partial or failure.writes else "blocked"
        else:
            state = {"verified": "completed", "unverified": "blocked"}.get(result["status"], result["status"])
        if state not in {"completed", "blocked", "partial"}:
            raise ValueError("Invalid progress terminal state.")
        self._emit(state)
        if self.output_failed:
            warnings = failure.warnings if failure is not None else result.setdefault("warnings", [])
            if IO_WARNING not in warnings:
                warnings.append(IO_WARNING)
            if self.shutdown_flush_unresolved and SHUTDOWN_WARNING not in warnings:
                warnings.append(SHUTDOWN_WARNING)


def reporting(workflow):
    """One reporter and terminal event across nested public entrypoints."""
    def decorate(function):
        @wraps(function)
        def wrapped(*args, progress=None, **kwargs):
            if progress is None:
                progress = Progress(workflow, enabled=False)
            outer = progress.depth == 0
            progress.depth += 1
            try:
                result = function(*args, progress=progress, **kwargs)
            except HelperFailure as failure:
                if outer:
                    progress.finish(failure=failure)
                raise
            else:
                if outer:
                    progress.finish(result=result)
                return result
            finally:
                progress.depth -= 1
        return wrapped
    return decorate


def add_progress_argument(parser):
    parser.add_argument("--no-progress", dest="progress", action="store_false",
                        help="Suppress content-free execution progress on stderr.")
