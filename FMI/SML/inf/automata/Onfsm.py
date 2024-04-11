from collections import defaultdict
from random import choice

from FMI.SML.inf.base import AutomatonState, Automaton


class OnfsmState(AutomatonState):

    def __init__(self, state_id):
        super().__init__(state_id)
        self.transitions = defaultdict(list)

    def add_transition(self, inp, out, new_state):
        self.transitions[inp].append((out, new_state))

    def get_transition(self, input, output=None):
        possible_transitions = self.transitions[input]
        if output:
            return next((t for t in possible_transitions if t[0] == output), None)
        else:
            return possible_transitions



class Onfsm(Automaton):

    def __init__(self, initial_state: OnfsmState, states: list):
        super().__init__(initial_state, states)

    def step(self, letter):

        transition = choice(self.current_state.transitions[letter])
        output = transition[0]
        self.current_state = transition[1]
        return output

    def outputs_on_input(self, letter):
        return [trans[0] for trans in self.current_state.transitions[letter]]

    def step_to(self, inp, out):
        for new_state in self.current_state.transitions[inp]:
            if new_state[0] == out:
                self.current_state = new_state[1]
                return out
        return None
    # TODO: look at this
    def get_shortest_path(self, origin_state, target_state):

        if origin_state not in self.states or target_state not in self.states:
            raise Exception("State not in the automaton")

        explored = set()
        queue = [[origin_state]]
        if origin_state == target_state:
            return ()
        count = 0
        while queue:
            path = queue.pop(0)
            node = path[-1]
            if node not in explored:
                neighbours = node.transitions.values()
                for neighbour in neighbours:
                    neig = neighbour[0][1]
                    new_path = list(path)
                    new_path.append(neig)
                    queue.append(new_path)
                    if neig == target_state:
                        acc_seq = new_path[:-1]
                        inputs = []
                        for ind, state in enumerate(acc_seq):
                            inputs.append(next(key for key, value in state.transitions.items()
                                               if value[0][1] == new_path[ind + 1]))
                        return tuple(inputs)
                explored.add(node)
        return ()
