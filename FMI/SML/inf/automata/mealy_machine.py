from FMI.SML.inf.base import AutomatonState, DeterministicAutomaton

class MealyState(AutomatonState):

    def __init__(self,state_id=None):
        super(MealyState, self).__init__(state_id)
        self.output_fun = dict()


class MealyMachine(DeterministicAutomaton):

    def __init__(self, initial_state, states):
        super(MealyMachine, self).__init__(initial_state, states)

    def step(self, letter):

        output = self.current_state.output_fun[letter] #TODO: fix this, might throw an error (revisit)
        self.current_state = self.current_state.transitions[letter]
        return output
