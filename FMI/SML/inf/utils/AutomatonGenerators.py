import random

from FMI.SML.inf.automata import MealyMachine, MealyState
from FMI.SML.inf.utils.HelperFunctions import random_string_generator


def generate_random_mealy_machine(num_states, input_alphabet, output_alphabet, compute_prefixes=False) -> MealyMachine:
    """
    Generates a random Mealy machine.

    Args:

        num_states: number of states
        input_alphabet: input alphabet
        output_alphabet: output alphabet
        compute_prefixes: if true, shortest path to reach each state will be computed (Default value = False)

    Returns:
        Mealy machine with num_states states

    """
    states = list()

    for i in range(num_states):
        states.append(MealyState(i))

    for state in states:
        for a in input_alphabet:
            state.transitions[a] = random.choice(states)
            state.output_fun[a] = random.choice(output_alphabet)

    mm = MealyMachine(states[0], states)
    if compute_prefixes:
        for state in states:
            state.prefix = mm.get_shortest_path(mm.initial_state, state)

    return mm

