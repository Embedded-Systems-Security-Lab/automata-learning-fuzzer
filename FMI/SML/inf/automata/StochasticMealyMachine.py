import random
from collections import defaultdict

from FMI.SML.inf.automata import MdpState, Mdp
from FMI.SML.inf.base import Automaton, AutomatonState

class StochasticMealyState(AutomatonState):
    def __init__(self, state_id):
        super().__init__(state_id)
        self.transitions = defaultdict(list)


class StochasticMealyMachine(Automaton):

    def __init__(self, initial_state: StochasticMealyState, states: list):
        super().__init__(initial_state, states)

    def reset_to_initial(self):
        self.current_state = self.initial_state

    def step(self, letter):

        prob = random.random()
        probability_distributions = [i[2] for i in self.current_state.transitions[letter]]
        index = 0
        for i, p in enumerate(probability_distributions):
            prob -= p
            if prob <= 0:
                index = i
                break

        transition = self.current_state.transitions[letter][index]
        self.current_state = transition[0]
        return transition[1]

    def step_to(self, inp, out):

        for (new_state, output, prob) in self.current_state.transitions[inp]:
            if output == out:
                self.current_state = new_state
                return out
        return None

    def to_mdp(self):
        return smm_to_mdp_conversion(self)

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
                # print(node.transitions.values())
                # exit()
                neighbours = node.transitions.values()

                for neighbour in neighbours:
                    neig = neighbour[0][0]
                    # print(neig, target_state)
                    new_path = list(path)
                    new_path.append(neig)
                    queue.append(new_path)
                    if neig == target_state:
                        acc_seq = new_path[:-1]
                        inputs = []
                        for ind, state in enumerate(acc_seq):
                            inputs.append(next(key for key, value in state.transitions.items()
                                               if value[0][0] == new_path[ind + 1]))
                        return tuple(inputs)
                explored.add(node)
        return ()

def smm_to_mdp_conversion(smm: StochasticMealyMachine):
    """
    Convert SMM to MDP.
    Args:
      smm: StochasticMealyMachine: SMM to convert
    Returns:
        equivalent MDP
    """
    inputs = smm.get_input_alphabet()
    mdp_states = []
    smm_state_to_mdp_state = dict()
    init_state = MdpState("0", "___start___")
    mdp_states.append(init_state)
    for s in smm.states:
        incoming_edges = defaultdict(list)
        incoming_outputs = set()
        for pre_s in smm.states:
            for i in inputs:
                incoming_edges[i] += filter(lambda t: t[0] == s, pre_s.transitions[i])
                incoming_outputs.update(map(lambda t: t[1], incoming_edges[i]))
        state_id = 0
        for o in incoming_outputs:
            new_state_id = s.state_id + str(state_id)
            state_id += 1
            new_state = MdpState(new_state_id, o)
            mdp_states.append(new_state)
            smm_state_to_mdp_state[(s.state_id, o)] = new_state

    for s in smm.states:
        mdp_states_for_s = {mdp_state for (s_id, o), mdp_state in smm_state_to_mdp_state.items() if s_id == s.state_id}
        for i in inputs:
            for outgoing_t in s.transitions[i]:
                target_smm_state = outgoing_t[0]
                output = outgoing_t[1]
                prob = outgoing_t[2]
                target_mdp_state = smm_state_to_mdp_state[(target_smm_state.state_id, output)]
                for mdp_state in mdp_states_for_s:
                    mdp_state.transitions[i].append((target_mdp_state, prob))
                if s == smm.initial_state:
                    init_state.transitions[i].append((target_mdp_state, prob))
    return Mdp(init_state, mdp_states)
