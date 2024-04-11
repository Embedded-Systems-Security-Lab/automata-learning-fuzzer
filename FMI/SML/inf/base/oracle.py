from abc import ABC, abstractmethod
#from FMI.SML.inf.base import SUL

class Oracle(ABC):

    def __init__(self, alphabet, sul):
        self.alphabet = alphabet
        self.sul = sul
        self.num_queries = 0
        self.num_steps = 0

    @abstractmethod
    def find_cex(self, hypothesis):
        pass

    def reset_hyp_and_sul(self, hypothesis):
        hypothesis.reset_to_initial()
        self.sul.post()
        self.sul.pre()
        self.num_queries += 1

    def update_alphabet(self, alphabet):
        self.alphabet = alphabet
