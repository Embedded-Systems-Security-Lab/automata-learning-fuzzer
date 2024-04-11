import time

from typing import Type, Any
from types import TracebackType


class Timer(object):

    def __init__(self) -> None:
        self.start_time = self.get_current_time()
        self.end_time = None

    def __enter__(self) -> Any:
        self.start_time = self.get_current_time()
        self.end_time = None
        return self

    def __exit__(self, exc_type: Type, exc_value: Exception, tb: TracebackType) ->None:
        self.end_time = self.get_current_time()

    def elapsed_time(self) -> float:
        return (self.end_time - self.start_time) if self.end_time else \
                (self.get_current_time() - self.start_time)


    def get_current_time(self) -> float:
        return time.perf_counter()
