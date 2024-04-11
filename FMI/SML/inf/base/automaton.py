from abc import ABC, abstractmethod
from collections import defaultdict
import uuid



class AutomatonState(ABC):

    def __init__(self, state_id=None):
        if not state_id:
            self.state_id = uuid.uuid4()
        else:
            self.state_id = state_id
        self.transitions = dict()
        self.prefix = None

    def get_diff_state_transitions(self):
        transitions = []
        for trans, state in self.transitions.items():
            if state != self:
                transitions.append(trans)
        return transitions

    def get_same_state_transitions(self):

        dst = self.get_diff_state_transitions()
        all_trans = set(self.transitions.key())
        return [t for t in all_trans if t not in dst]

    def __str__(self):
        return "state_id: {}".format(self.state_id)

class Automaton(ABC):

    def __init__(self, initial_state, states):
        self.initial_state = initial_state
        self.states = states
        self.current_state = initial_state
        self.size = len(states)
        self.characterization_set: list = []

    def reset_to_initial(self):
        self.current_state = self.initial_state

    @abstractmethod
    def step(self, letter):
        pass

    def is_input_complete(self):

        alphabet = set(self.get_input_alphabet())
        for state in self.states:
            if set(state.transitions.keys()) != alphabet:
                return False
        return True

    def get_input_alphabet(self) -> list:
        alphabet = list() #TODO: change this later to set
        for s in self.states:
            for i in s.transitions:
                if i not in alphabet:
                    alphabet.append(i)
        return alphabet

    def get_state_by_id(self, state_id):
        for state in self.states:
            if state.stat_id == state_id:
                return state

    def __str__(self):
        """
        :return: A string representation of the automaton
        """
        from FMI.SML.inf.utils import save_automaton_to_file
        return save_automaton_to_file(self, path='learnedModel', file_type='string', round_floats=2)

    def execute_sequence(self, origin_state, seq):
        self.current_state = origin_state
        return [self.step(s) for s in seq]
    # @abstractmethod
    # def get_shortest_path(self, origin_state, target_state):
    #     pass

class DeterministicAutomaton(Automaton):

    def get_shortest_path(self, origin_state, target_state):

        if origin_state not in self.states or target_state not in self.states:
            raise Exception("State not in the automaton")

        explored = set()
        queue = [[origin_state]]
        if origin_state == target_state:
            return ()
        while queue:
            path = queue.pop(0)
            node = path[-1]
            if node not in explored:
                neighbours = node.transitions.values()
                for neighbour in neighbours:
                    new_path = list(path)
                    new_path.append(neighbour)
                    queue.append(new_path)
                    if neighbour == target_state:
                        acc_seq = new_path[:-1]
                        inputs = []
                        for ind, state in enumerate(acc_seq):
                            inputs.append(next(key for key, value in state.transitions.items()
                                               if value == new_path[ind + 1]))
                        return tuple(inputs)

                explored.add(node)

        return ()

    @abstractmethod
    def step(self, letter):
        pass

    def is_strongly_connected(self):
        import itertools
        state_comb_list = itertools.permutations(self.states, 2)
        for state_comb in state_comb_list:
            if not self.get_shortest_path(state_comb[0], state_comb[1]):
                return False
        return True

    def output_step(self, state, letter):
        state_save = self.current_state
        self.current_state = state
        output = self.step(letter)
        self.current_state = state_save
        return output

    def compute_output_seq(self, state, sequence):
        state_save = self.current_state
        output = self.execute_sequence(state, sequence)
        self.current_state = state_save
        return output

    def find_distinguishing_seq(self, state1, state2):
        visited = set()
        to_explore = [(state1, state2, [])]
        alphabet = self.get_input_alphabet()
        while to_explore:
            (curr_s1, curr_s2, prefix) = to_explore.pop(0)
            visited.add((curr_s1, curr_s2))
            for i in alphabet:
                o1 = self.output_step(curr_s1, i)
                o2 = self.output_step(curr_s2, i)
                new_prefix = prefix + [i]
                if o1 != o2:
                    return new_prefix
                else:
                    next_s1 = curr_s1.transitions[i]
                    next_s2 = curr_s2.transitions[i]
                    if (next_s1, next_s2) not in visited:
                        to_explore.append((next_s1, next_s2, new_prefix))

        raise SystemExit('Distinguishing sequence could not be computed (Non-canonical automaton).')

    def compute_characterization_set(self, char_set_init=None, online_suffix_closure=True, split_all_blocks=True):
        from copy import copy

        blocks = list()
        blocks.append(copy(self.states))
        char_set = [] if not char_set_init else char_set_init
        if char_set_init:
            for seq in char_set_init:
                blocks = self._split_blocks(blocks, seq)

        while True:
            # Given a partition (of states), this function returns a block with at least two elements.
            try:
                block_to_split = next(filter(lambda b: len(b) > 1, blocks))
            except StopIteration:
                block_to_split = None

            if not block_to_split:
                break
            split_state1 = block_to_split[0]
            split_state2 = block_to_split[1]
            dist_seq = self.find_distinguishing_seq(split_state1, split_state2)
            assert ((not split_all_blocks) or (dist_seq not in char_set))

            # in L*-based learning, we use suffix-closed column labels, so it makes sense to use a suffix-closed
            # char set in this context
            if online_suffix_closure:
                dist_seq_closure = [tuple(dist_seq[len(dist_seq) - i - 1:]) for i in range(len(dist_seq))]
            else:
                dist_seq_closure = [tuple(dist_seq)]

            # the standard approach described by Gill, computes a sequence that splits one block and really only splits
            # one block, that is, it is only applied to the states in said block
            # in L*-based learning we combine every prefix with every, therefore it makes sense to apply the sequence
            # on all blocks and split all
            if split_all_blocks:
                for seq in dist_seq_closure:
                    # seq may be in char_set if we do the closure on the fly
                    if seq in char_set:
                        continue
                    char_set.append(seq)
                    blocks = self._split_blocks(blocks, seq)
            else:
                blocks.remove(block_to_split)
                new_blocks = [block_to_split]
                for seq in dist_seq_closure:
                    char_set.append(seq)
                    new_blocks = self._split_blocks(new_blocks, seq)
                for new_block in new_blocks:
                    blocks.append(new_block)

        char_set = list(set(char_set))
        return char_set

    def _split_blocks(self, blocks, seq):

        new_blocks = []
        for block in blocks:
            block_after_split = defaultdict(list)
            for state in block:
                output_seq = tuple(self.compute_output_seq(state, seq))
                block_after_split[output_seq].append(state)
            for new_block in block_after_split.values():
                new_blocks.append(new_block)
        return new_blocks

















