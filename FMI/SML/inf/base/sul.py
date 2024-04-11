from abc import ABC, abstractmethod
from FMI.SML.inf.base.cache_tree import CacheTree
from FMI.SML.inf.base.trace_tree import TraceTree
from FMI.SML.inf.utils.stats import Stats

class SUL(ABC):

    def __init__(self):
        self.stats = Stats()

    def query(self, word):

        self.pre()
        if len(word) == 0:
            out = [self.step(None)]
        else:
            out = [self.step(letter) for letter in word]
        self.post()
        self.stats.num_queries += 1
        self.stats.num_submitted_letter += len(word)
        return out

    @abstractmethod
    def pre(self):
        pass

    @abstractmethod
    def post(self):
        pass

    @abstractmethod
    def step(self, letter):
        pass


class CacheSUL(SUL):

    def __init__(self, sul:SUL):
        super(CacheSUL, self).__init__()
        self.sul = sul
        self.cache = CacheTree()

    def query(self, word):

        cached_query = self.cache.in_cache(word)
        self.stats.num_queries += 1
        self.stats.num_letter += len(word)
        if cached_query:
            self.stats.num_cached_queries += 1
            return cached_query

        out = self.sul.query(word)

        self.cache.reset()
        # Store value in a cache tree for later use
        for i, o in zip(word, out):
            self.cache.step(i,o)
        self.stats.num_submitted_queries += 1
        self.stats.num_submitted_letter += len(word)
        return out

    def pre(self):
        self.cache.reset()
        self.sul.pre()

    def post(self):
        self.sul.post()

    def step(self, letter):
        out = self.sul.step(letter)
        #save in cache
        self.cache.step(letter, out)
        return out


class NonDeterministicSULWrapper(SUL):
    """
    Wrapper for non-deterministic SUL. After every step, input/output pair is added to the tree containing all traces.
    """

    def __init__(self, sul: SUL):
        super().__init__()
        self.sul = sul
        self.cache = TraceTree()

    def pre(self):
        self.cache.reset()
        self.sul.pre()

    def post(self):
        self.sul.post()

    def step(self, letter):
        out = self.sul.step(letter)
        self.cache.add_to_tree(letter, out)
        return out

