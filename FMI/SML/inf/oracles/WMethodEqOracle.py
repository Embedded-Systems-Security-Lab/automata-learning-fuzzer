from FMI.SML.inf.base import Oracle, SUL, CacheSUL
from itertools import combinations, product
from random import shuffle, choice, randint


class WMethodEqOracle(Oracle):

    def __init__(self, alphabet: list, sul: SUL, max_number_of_states, shuffle_test_set=True):
        super(WMethodEqOracle, self).__init__(alphabet, sul)
        self.m = max_number_of_states
        self.shuffle = shuffle_test_set
        self.cache = set()

    def find_cex(self, hypothesis):

        if not hypothesis.characterization_set:
            hypothesis.characterization_set = hypothesis.compute_characterization_set()

        transition_cover = [state.prefix + (letter,) for state in hypothesis.states for letter in self.alphabet]

        middle = []
        for i in range(self.m - len(hypothesis.states)):
            middle.extend(combinations(self.alphabet, i + 1))

        test_set = []
        for seq in product(transition_cover, middle, hypothesis.characterization_set):
            inp_seq = tuple([i for sub in seq for i in sub])
            if inp_seq not in self.cache:
                test_set.append(inp_seq)

        if self.shuffle:
            shuffle(test_set)
        else:
            test_set.sort(key=len, reverse=True)

        for seq in test_set:
            self.reset_hyp_and_sul(hypothesis)
            outputs = []

            for ind, letter in enumerate(seq):
                out_hyp = hypothesis.step(letter)
                out_sul = self.sul.step(letter)
                self.num_steps += 1

                outputs.append(out_sul)
                if out_hyp != out_sul:
                    self.sul.post()
                    return seq[:ind + 1]
            self.cache.add(seq)

        return None


class RandomWMethodEqOracle(Oracle):

    def __init__(self, alphabet: list, sul: SUL, walks_per_state=10, walk_len=20):

        super().__init__(alphabet, sul)
        self.walks_per_state = walks_per_state
        self.random_walk_len = walk_len
        self.freq_dict = dict()

    def find_cex(self, hypothesis):

        if not hypothesis.characterization_set:
            hypothesis.characterization_set = hypothesis.compute_characterization_set()

        states_to_cover = []
        for state in hypothesis.states:
            if state.prefix is None:
                state.prefix = hypothesis.get_shortest_path(hypothesis.initial_state, state)
            if state.prefix not in self.freq_dict.keys():
                self.freq_dict[state.prefix] = 0

            states_to_cover.extend([state] * (self.walks_per_state - self.freq_dict[state.prefix]))

        shuffle(states_to_cover)

        for state in states_to_cover:
            self.freq_dict[state.prefix] = self.freq_dict[state.prefix] + 1

            self.reset_hyp_and_sul(hypothesis)

            prefix = state.prefix
            random_walk = tuple(choice(self.alphabet) for _ in range(randint(1, self.random_walk_len)))

            test_case = prefix + random_walk + choice(hypothesis.characterization_set)

            for ind, i in enumerate(test_case):
                output_hyp = hypothesis.step(i)
                output_sul = self.sul.step(i)
                self.num_steps += 1

                if output_sul != output_hyp:
                    self.sul.post()
                    return test_case[:ind + 1]

        return None
