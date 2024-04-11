import abc
from typing import Dict

from FMI.session import Session


class IFuzzer(abc.ABC):
    """Describes a fuzzer interface.
    """

    name = 'Implement'
    init_corpus = None

    @staticmethod
    @abc.abstractmethod
    def get_corpus(session: Session):
        """Get possible requests"""
        raise NotImplementedError("Subclasses should implement this!")

    @staticmethod
    @abc.abstractmethod
    def initialize(*args, **kwargs) -> None:
        """Get possible requests"""
        raise NotImplementedError("Subclasses should implement this!")
