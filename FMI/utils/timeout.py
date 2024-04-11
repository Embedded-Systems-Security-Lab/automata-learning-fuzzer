import time

from typing import Type, Any, Union, Optional

from types import FrameType, TracebackType


class SignalTimeout(object):

    def __init__(self, time_out: Union[int, float]) -> None:
        self.time_out = time_out
        self.old_handler = signal.SIG_DFL
        self.old_timeout = 0.0

    def __enter__(self) -> Any:
        self.old_handler = signal.signal(signal.SIGALRM, self._timeout_handler)
        self.old_timeout, _ = signal.setitimer(signal.ITIMER_REAL, self.timeout)
        return self

    def __exit__(self, exc_type: Type, exc_value: Exception, tb: TracebackType) -> None:
        self._cancel()


    def _cancel(self) -> None:
        signal.signal(signal.SIGALRM, self.old_handler)
        signal.setitimer(signal.ITIMER_REAL, self.old_timeout)


    def _timeout_handler(self, signum: int, frame: Optional[FrameType]) -> None:
        """TODO: Something that might complete here"""
        raise TimeoutError()
