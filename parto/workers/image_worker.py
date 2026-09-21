# parto/workers/image_worker.py
"""
Parto v0.3.0 - Multithreaded Image Task Worker
Keeps GUI responsive by running compute-intensive operations off the main thread.
Author: Ali Kamrani (MRThugh)
"""

from __future__ import annotations
from typing import Callable, Any, Optional
from PySide6.QtCore import QThread, Signal, QObject


class ImageWorkerThread(QThread):
    """
    Dedicated background thread for compute-heavy image transformations,
    filters, large resizes, or export encoding.
    """
    finished = Signal(object)  # Emits result on completion
    error = Signal(str)        # Emits error message if failed
    progress = Signal(int)     # Emits percentage progress if applicable

    def __init__(
        self,
        task_fn: Callable[..., Any],
        *args: Any,
        parent: Optional[QObject] = None,
        **kwargs: Any,
    ):
        super().__init__(parent)
        self.task_fn = task_fn
        self.args = args
        self.kwargs = kwargs

    def run(self) -> None:
        try:
            result = self.task_fn(*self.args, **self.kwargs)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class AsyncOperationRunner(QObject):
    """
    Manages starting background workers and wiring completion/error handlers.
    """

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._current_worker: Optional[ImageWorkerThread] = None

    def is_running(self) -> bool:
        return self._current_worker is not None and self._current_worker.isRunning()

    def run_task(
        self,
        task_fn: Callable[..., Any],
        *args: Any,
        on_success: Optional[Callable[[Any], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
        **kwargs: Any,
    ) -> ImageWorkerThread:
        """Start task on a background worker thread."""
        if self.is_running():
            # Wait or terminate existing if necessary
            self._current_worker.wait(500)

        worker = ImageWorkerThread(task_fn, *args, **kwargs)
        self._current_worker = worker

        if on_success:
            worker.finished.connect(on_success)
        if on_error:
            worker.error.connect(on_error)

        worker.finished.connect(self._cleanup)
        worker.error.connect(self._cleanup)

        worker.start()
        return worker

    def _cleanup(self, *_: Any) -> None:
        if self._current_worker is not None:
            self._current_worker.deleteLater()
            self._current_worker = None
