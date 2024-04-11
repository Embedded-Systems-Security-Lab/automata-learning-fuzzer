import time

from FMI.SML.inf.base import Oracle, SUL, CacheSUL, NonDeterministicSULWrapper
from FMI.SML.inf.utils.HelperFunctions import extend_set, print_learning_info, print_observation_table, all_suffixes
from .n_d_observation_table import NDObservationTable
from FMI.utils.time import Timer
from FMI.SML.inf.utils import visualize_automaton


print_options = [0, 1, 2, 3]


class NDLStar(object):

    def __init__(self,alphabet: list, sul: SUL, eq_oracle: Oracle, n_sampling=3, samples=None, stochastic=False):
        self.alphabet = alphabet
        self.eq_oracle = eq_oracle
        self.samples = samples
        self.stochastic = stochastic
        #self.automaton_type = automaton_type
        if not isinstance(sul, NonDeterministicSULWrapper):
            self.sul = NonDeterministicSULWrapper(sul)

        else:
            self.sul = sul
        if samples:
            for inputs, outputs in samples:
                self.sul.cache.add_trace(inputs, outputs)
        self.eq_oracle.sul = self.sul

        self.n_sampling = n_sampling
        self.observation_table = NDObservationTable(self.alphabet, self.sul, self.n_sampling)
        self.hypothesis = None
        self.last_cex = None


    # TODO: Change this and think about this
    def update_values(self, alphabet):
        self.alphabet.extend(alphabet)
        self.observation_table = NDObservationTable(self.alphabet, self.sul, self.n_sampling)
        self.hypothesis = None
        self.last_cex = None

    def get_hypothesis(self):
        #
        if self.hypothesis is None:
            try:
                self.hypothesis = self.observation_table.gen_hypothesis(check_for_duplicate_rows=self.cex_processing is None)
            except:
                raise Exception

        return self.hypothesis

    def visiualize_automata(self):
        if self.hypothesis:
            visualize_automaton(self.hypothesis)


    def run(self,min_rounds=None,max_rounds=10,print_level=3,return_data=True):

        eq_query_time = 0
        learning_rounds = 0
        self.hypothesis = None
        self.last_cex = None

        # Initial update of observation table, for empty row
        with Timer() as t:
            while True:
                learning_rounds += 1
                print(learning_rounds)
                if max_rounds and learning_rounds - 1 == max_rounds:
                    break
                # Make observation table consistent (iff there is no counterexample processing)
                self.observation_table.S = list()
                self.observation_table.S.append((tuple(), tuple()))
                self.observation_table.query_missing_observations()

                row_to_close = self.observation_table.get_row_to_close()
                while row_to_close is not None:
                    print("Closing the following row: {}".format(row_to_close))
                    self.observation_table.query_missing_observations()
                    row_to_close = self.observation_table.get_row_to_close()
                    self.observation_table.clean_obs_table()

                self.hypothesis = self.observation_table.gen_hypothesis()
                print("Finished closing the rows")
                if counterexample_not_valid(self.hypothesis, self.last_cex):
                    cex = self.sul.cache.find_cex_in_cache(self.hypothesis)

                    if cex is None:
                        learning_rounds += 1
                        # Find counterexample
                        if print_level > 1:
                            print(f'Hypothesis {learning_rounds}: {len(self.hypothesis.states)} states.')

                        if print_level == 3:
                            print_observation_table(self.observation_table, 'non-det')
                        eq_query_start = time.time()
                        cex = self.eq_oracle.find_cex(self.hypothesis)
                        eq_query_time += time.time() - eq_query_start

                    self.last_cex = cex
                else:
                    cex = self.last_cex
                print("Processing the following {}".format(cex))

                if cex is None:
                    break
                else:
                    print("Processing counter-example")
                    cex_suffixes = all_suffixes(cex[0])
                    for suffix in cex_suffixes:
                        if suffix not in self.observation_table.E:
                            self.observation_table.E.append(suffix)
                            break

        total_time = t.elapsed_time()
        eq_query_time = round(eq_query_time, 2)
        learning_time = round(total_time - eq_query_time, 2)


        info = {
            'learning_rounds': learning_rounds,
            'automaton_size': len(self.hypothesis.states),
            'queries_learning': self.sul.stats.num_queries,
            'steps_learning': self.sul.stats.num_letter,
            'queries_eq_oracle': self.eq_oracle.num_queries,
            'steps_eq_oracle': self.eq_oracle.num_steps,
            'learning_time': learning_time,
            'eq_oracle_time': eq_query_time,
            'total_time': total_time
        }

        if print_level > 0:
            print_learning_info(info)

        if return_data:
            return self.hypothesis, info

        return self.hypothesis, None

def counterexample_not_valid(hypothesis, cex):
    if cex is None:
        return True
    hypothesis.reset_to_initial()
    for i, o in zip(cex[0], cex[1]):
        out = hypothesis.step_to(i, o)
        if out is None:
            return False
    return True
