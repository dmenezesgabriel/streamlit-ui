import asyncio
import threading
from typing import Any, Coroutine, TypeVar

T = TypeVar("T")


class GlobalLoopContext:
    """
    Manages a global asyncio loop running in a background thread.
    This allows async resources (like MCP clients) to persist across Streamlit reruns.
    """

    _loop: asyncio.AbstractEventLoop
    _thread: threading.Thread
    _started: bool = False

    def __init__(self):
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)

    def _run_loop(self):
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def start(self):
        if not self._started:
            self._thread.start()
            self._started = True

    def run_coroutine(self, coro: Coroutine[Any, Any, T]) -> T:
        """
        Submits a coroutine to the background loop and waits for the result (thread-safe).
        This bridges the synchronous Streamlit script with the async background loop.
        """
        if not self._started:
            self.start()

        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result()

    def stop(self):
        if self._started:
            self._loop.call_soon_threadsafe(self._loop.stop)
            self._thread.join()
            self._started = False
