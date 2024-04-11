from collections import defaultdict

from FMI.utils.decorators import FMILogger
from FMI.SML.inf.base import Automaton, SUL
from FMI.SML.inf.automata import MealyState, MealyMachine


closing_options = ['shortest_first', 'longest_first', 'single']

@FMILogger
class ObservationTable(object):

    def __init__(self, alphabets, sul):
        if not alphabets:
            raise Exception("Alphabet cannot be empty")
        if not sul:
            raise Exception("SUL cannot be empty")

        self.sul = sul
        self.initialize(alphabets)

    def initialize(self, alphabets):
        self.alphabets = [tuple([a]) for a in alphabets]
        self.S = list()
        self.E = [tuple([a]) for a in alphabets]
        self.T = defaultdict(tuple)
        empty_word = tuple()
        self.S.append(empty_word)

    def get_rows_to_close(self, closing_strategy='longest_first'):
        assert closing_strategy in closing_options
        rows_to_close = []
        row_values = set()

        s_rows = {self.T[s] for s in self.S}

        for t in self.s_dot_a():
            row_t = self.T[t]
            if row_t not in s_rows and row_t not in row_values:
                rows_to_close.append(t)
                row_values.add(row_t)

                if closing_strategy == 'single':
                    return rows_to_close

        if not rows_to_close: return None

        if closing_strategy == 'longest_first': rows_to_close.reverse()

        return rows_to_close

    def get_causes_of_inconsistency(self):

        causes_of_inconsistency = set()
        for i, s1 in enumerate(self.S):
            for s2 in self.S[i + 1:]:
                if self.T[s1] == self.T[s2]:
                    for a in self.A:
                        if self.T[s1 + a] != self.T[s2 + a]:
                            for index, e in enumerate(self.E):
                                if self.T[s1 + a][index] != self.T[s2 + a][index]:
                                    causes_of_inconsistency.add(a + e)

        if not causes_of_inconsistency:
            return None
        return causes_of_inconsistency

    def update_obs_table(self, s_set: list = None, e_set: list = None):

        update_S = s_set if s_set else list(self.S) + list(self.s_dot_a())
        update_E = e_set if e_set else self.E

        # This could save few queries
        update_S.reverse()

        for s in update_S:
            for e in update_E:
                if len(self.T[s]) < len(self.E):
                    output = self.sul.query(s + e)
                    self.T[s] += (output[-1],)

    def s_dot_a(self):
        s_set = set(self.S)
        for s in self.S:
            for a in self.alphabets:
                if s + a not in s_set:
                    yield s + a

    def gen_hypothesis(self, check_for_duplicate_rows=False):

        state_distinguish = dict()
        states_dict = dict()
        initial_state = None

        if check_for_duplicate_rows:
            rows_to_delete = set()
            for i, s1 in enumerate(self.S):
                for s2 in self.S[i + 1:]:
                    if self.T[s1] == self.T[s2]:
                        rows_to_delete.add(s2)

            for row in rows_to_delete:
                self.S.remove(row)

        # create states based on S set
        stateCounter = 0
        for prefix in self.S:
            state_id = f's{stateCounter}'
            states_dict[prefix] = MealyState(state_id)

            states_dict[prefix].prefix = prefix
            state_distinguish[tuple(self.T[prefix])] = states_dict[prefix]

            if not prefix:
                initial_state = states_dict[prefix]
            stateCounter += 1

        # add transitions based on extended S set
        for prefix in self.S:
            for a in self.alphabets:
                state_in_S = state_distinguish[self.T[prefix + a]]
                states_dict[prefix].transitions[a[0]] = state_in_S
                #if self.automaton_type == 'mealy':
                states_dict[prefix].output_fun[a[0]] = self.T[prefix][self.E.index(a)]



        automaton = MealyMachine(initial_state, list(states_dict.values()))
        automaton.characterization_set = self.E

        return automaton



    def shrink(self, hypothesis):
        'WIP'
        init_set = []
        init_set.extend(self.alphabets)
        e_set = hypothesis.compute_characterization_set(char_set_init=init_set)
        ordered_e_set = list(init_set)
        ordered_e_set.extend([el for el in e_set if el not in init_set])

        self.T.clear()
        self.E = ordered_e_set

        for s in list(self.S) + list(self.s_dot_a()):
            for e in self.E:
                out = hypothesis.execute_sequence(hypothesis.initial_state, s + e)
                self.T[s] += (out[-1],)

        incons = self.get_causes_of_inconsistency()
        self._logger.debug("INCONSISTENCY: {}".format(incons))
        clos = self.get_rows_to_close()
        self._logger.debug("CLOSEDNESS: {}".format(clos))

class Akin_ObservationTable(ObservationTable):

    def __init__(self, alphabets, sul):
        super(Akin_ObservationTable).__init__(alphabets, sul)


    def update_obs_table(self, s_set: list = None, e_set: list = None):

        update_S = s_set if s_set else list(self.S) + list(self.s_dot_a())
        update_E = e_set if e_set else self.E

        # This could save few queries
        update_S.reverse()

        for s in update_S:
            for e in update_E:
                if len(self.T[s]) < len(self.E):
                    try:
                        output = self.sul.query(s + e)
                        self.T[s] += (output[-1],)
                    except:
                        self.refresh_table(s,e)

    def refresh_table(self, s_entry, e_entry):
        # print(f'refresh table on {s_entry + e_entry}')
        s_entries = [s_entry[:i] for i in range(len(s_entry))]
        for s in s_entries:
            for i,e in enumerate(self.E):
                error_counter = 0
                while error_counter < 3:
                    try:
                        if len(self.T[s]) >= (i + 1):
                            print(f'query {i}: {s + e}')
                            output = self.sul.query(s + e)
                            self.T[s] = self.T[s][:i] + (output[-1],) + self.T[s][(i + 1):]
                        break
                    except:
                        error_counter += 1
                        if error_counter == 3:
                            raise

        if len(self.T[s_entry]) < len(self.E):
            # print(f'query: {s_entry + e_entry}')
            output = self.sul.query(s_entry + e_entry)
            # print("passed this")
            self.T[s_entry] += (output[-1],)
