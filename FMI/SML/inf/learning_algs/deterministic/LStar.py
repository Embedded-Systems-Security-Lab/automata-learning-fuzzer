import time

from FMI.SML.inf.base import Oracle, SUL, CacheSUL
from FMI.SML.inf.non_deterministic_cache import NonDetCacheSUL
from FMI.SML.inf.utils.HelperFunctions import extend_set, print_learning_info, print_observation_table, all_prefixes
from .CounterExampleProcessing import longest_prefix_cex_processing, rs_cex_processing
from .observation_table import ObservationTable
from FMI.utils.time import Timer
from FMI.SML.inf.utils import visualize_automaton
from FMI.utils.exception import FMITableError

counterexample_processing_strategy = [None, 'rs', 'longest_prefix']
closedness_options = ['prefix', 'suffix']
print_options = [0, 1, 2, 3]


class LStar(object):

    def __init__(self,alphabet: list, sul: SUL, eq_oracle: Oracle,
                  closing_strategy='longest_first', cex_processing='rs', suffix_closedness=True, closedness_type='suffix'):
        self.alphabet = alphabet
        self.eq_oracle = eq_oracle
        #self.automaton_type = automaton_type
        self.closing_strategy = closing_strategy
        self.cex_processing = cex_processing
        self.suffix_closedness = suffix_closedness
        self.closedness_type = closedness_type
        # if cache_and_non_det_check and not isinstance(sul, NonDetCacheSUL):
        #     self.sul = NonDetCacheSUL(sul)
        #     self.eq_oracle.sul = sul
        # else:
        self.sul = sul
        # self.cache_and_non_det_check = cache_and_non_det_check
        self.observation_table = ObservationTable(self.alphabet, self.sul)
        self.hypothesis = None

    # TODO: Change this
    def update_values(self, alphabet):
        self.alphabet.extend(alphabet)
        self.observation_table = ObservationTable(self.alphabet, self.sul)

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


    def run(self,min_rounds=None,max_rounds=None,print_level=3,return_data=True):

        eq_query_time = 0
        learning_rounds = 0
        self.hypothesis = None
        # Initial update of observation table, for empty row
        with Timer() as t:
            self.observation_table.update_obs_table()
            while True:
                learning_rounds += 1
                if max_rounds and learning_rounds - 1 == max_rounds:
                    break
                # Make observation table consistent (iff there is no counterexample processing)
                if not self.cex_processing:
                    inconsistent_rows = self.observation_table.get_causes_of_inconsistency()
                    while inconsistent_rows is not None:
                        extend_set(self.observation_table.E, inconsistent_rows)
                        self.observation_table.update_obs_table(e_set=inconsistent_rows)
                        inconsistent_rows = self.observation_table.get_causes_of_inconsistency()

                # Close observation table
                rows_to_close = self.observation_table.get_rows_to_close(self.closing_strategy)
                while rows_to_close is not None:
                    rows_to_query = []
                    for row in rows_to_close:
                        self.observation_table.S.append(row)
                        rows_to_query.extend([row + (a,) for a in self.alphabet])
                    self.observation_table.update_obs_table(s_set=rows_to_query)
                    rows_to_close = self.observation_table.get_rows_to_close(self.closing_strategy)

                # Generate hypothesis
                self.hypothesis = self.observation_table.gen_hypothesis(check_for_duplicate_rows=self.cex_processing is None)
                if print_level > 1:
                    print(f'Hypothesis {learning_rounds}: {len(self.hypothesis.states)} states.')

                if print_level == 3:
                    print_observation_table(self.observation_table, 'det')
                try:
                # Find counterexample
                    eq_query_start = time.time()
                    cex = self.eq_oracle.find_cex(self.hypothesis)
                    eq_query_time += time.time() - eq_query_start

                    # If no counterexample is found, return the hypothesis
                    if cex is None:
                        break

                    if print_level == 3:
                        print('Counterexample', cex)
                    # Process counterexample and ask membership queries
                    if not self.cex_processing:
                        s_to_update = []
                        added_rows = extend_set(self.observation_table.S, all_prefixes(cex))
                        s_to_update.extend(added_rows)
                        for p in added_rows:
                            s_to_update.extend([p + (a,) for a in self.alphabet])

                        self.observation_table.update_obs_table(s_set=s_to_update)
                        continue
                    elif self.cex_processing == 'longest_prefix':
                        cex_suffixes = longest_prefix_cex_processing(self.observation_table.S + list(self.observation_table.s_dot_a()),
                                                                     cex, self.closedness_type)
                    else:
                        cex_suffixes = rs_cex_processing(self.sul, cex, self.hypothesis, self.suffix_closedness, self.closedness_type)
                    added_suffixes = extend_set(self.observation_table.E, cex_suffixes)
                    self.observation_table.update_obs_table(e_set=added_suffixes)
                except FMITableError:
                    self.observation_table.update_obs_table()
                print(learning_rounds)

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
            'total_time': total_time,
            'characterization set': self.observation_table.E
        }
        # if self.cache_and_non_det_check:
        #     info['cache_saved'] = self.sul.stats.num_cached_queries

        if print_level > 0:
            print_learning_info(info)

        if return_data:
            return self.hypothesis, info

        return self.hypothesis, None
