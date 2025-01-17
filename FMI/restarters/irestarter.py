import abc

class IRestarter(object, metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def __init__(self, *args, **kwargs):
        pass

    @staticmethod
    @abc.abstractmethod
    def name() -> str:
        """Get name"""
        pass

    @staticmethod
    @abc.abstractmethod
    def help():
        """ Get help string"""
        pass

    @abc.abstractmethod
    def restart(self, *args, **kwargs) -> str or None:
        """Restart the target with magic"""
        pass

    @abc.abstractmethod
    def kill(self):
        pass

    @abc.abstractmethod
    def healthy(self) -> bool:
        pass
