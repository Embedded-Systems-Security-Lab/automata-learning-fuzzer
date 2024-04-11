from abc import ABC, abstractmethod

class Mutation(ABC):

    def __init__(self,seed):
        self.seed = seed

    @abstractmethod
    def get_mutated_payload(self,mut_input):
        pass
