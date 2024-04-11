import time

from FMI.SML.inf.base import SUL, Oracle
from FMI.SML.inf.learning_algs.stochastic.DifferenceChecker import AdvancedHoeffdingChecker, HoeffdingChecker, \
    ChiSquareChecker, DifferenceChecker
from FMI.SML.inf.learning_algs.stochastic.SamplingBasedObservationTable import SamplingBasedObservationTable
from FMI.SML.inf.learning_algs.stochastic.StochasticCexProcessing import stochastic_longest_prefix, stochastic_rs
from FMI.SML.inf.learning_algs.stochastic.StochasticTeacher import StochasticTeacher
from FMI.SML.inf.utils.HelperFunctions import print_learning_info, print_observation_table, get_cex_prefixes, \
    get_available_oracles_and_err_msg

from FMI.SML.inf.utils.ModelChecking import stop_based_on_confidence
from FMI.SML.inf.utils import visualize_automaton

strategies = ['classic', 'normal', 'chi2']
cex_sampling_options = [None, 'bfs']
cex_processing_options = [None, 'longest_prefix', 'rs']
print_options = [0, 1, 2, 3]
diff_checker_options = {'classic': HoeffdingChecker(),
                        'chi2': ChiSquareChecker(),
                        'normal': AdvancedHoeffdingChecker()}
available_oracles, available_oracles_error_msg = get_available_oracles_and_err_msg()

class StochasticLStar(object):

    def __init__(self, alphabet: list, sul: SUL, eq_oracle: Oracle,target_unambiguity=0.99,
                 automaton_type='mdp', strategy='normal', cex_processing=None, samples_cex_strategy=None,
                 stopping_range_dict='strict', custom_oracle=False, property_based_stopping=None, n_c=20, n_resample=100):

        assert samples_cex_strategy in cex_sampling_options or samples_cex_strategy.startswith('random')
        assert cex_processing in cex_processing_options
        self.cex_processing = cex_processing
        assert automaton_type in {'mdp', 'smm'}
        self.automaton_type = automaton_type
        if not isinstance(stopping_range_dict, dict):
            assert stopping_range_dict in {'strict', 'relaxed'}
        if property_based_stopping:
            assert len(property_based_stopping) == 3
        self.property_based_stopping = property_based_stopping

        if strategy in diff_checker_options:
            compatibility_checker = diff_checker_options[strategy]
        else:
            assert isinstance(strategy, DifferenceChecker)
            compatibility_checker = strategy

        if not custom_oracle and type(eq_oracle) not in available_oracles:
            raise SystemExit(available_oracles_error_msg)

        if stopping_range_dict == 'strict':
            self.stopping_range_dict = {12: 0.001, 18: 0.002, 25: 0.005, 30: 0.01, 35: 0.02}
        elif stopping_range_dict == 'relaxed':
            self.stopping_range_dict = {7: 0.001, 12: 0.003, 17: 0.005, 22: 0.01, 28: 0.02}

        self.eq_oracle = eq_oracle
        self.stochastic_teacher = StochasticTeacher(sul, n_c, self.eq_oracle, automaton_type, compatibility_checker,
                                               samples_cex_strategy=samples_cex_strategy)

        # This way all steps from eq. oracle will be added to the tree

        self.eq_oracle.sul = self.stochastic_teacher.sul
        self.sul = self.stochastic_teacher.sul
        self.observation_table = SamplingBasedObservationTable(alphabet, automaton_type,
                                                          self.stochastic_teacher, compatibility_checker=compatibility_checker,
                                                          strategy=strategy,
                                                          cex_processing=cex_processing)
        self.hypothesis = None
        self.target_unambiguity = target_unambiguity
        self.n_resample = n_resample

    def get_hypothesis(self):
        if self.hypothesis is None:
            try:
                self.hypothesis = self.observation_table.gen_hypothesis()
            except:
                raise Exception

        return self.hypothesis

    def visiualize_automata(self):
        if self.hypothesis:
            visualize_automaton(self.hypothesis)

    def run(self,min_rounds=3, max_rounds=5,print_level=3,return_data=True):
        start_time = time.time()
        eq_query_time = 0

        # Ask queries for non-completed cells and update the observation table
        self.observation_table.refine_not_completed_cells(self.n_resample, uniform=True)
        self.observation_table.update_obs_table_with_freq_obs()

        learning_rounds = 0

        while True:
            learning_rounds += 1
            #TODO: Bad programming, a hack for now to get out proof of concept
            self.sul.sul.update_learning_round(learning_rounds)
            print("The learning round is {}".format(learning_rounds))

            self.observation_table.make_closed_and_consistent()

            self.hypothesis = self.observation_table.generate_hypothesis()

            self.observation_table.trim(self.hypothesis)

            # If there is no chaos state is not reachable, remove it from state set
            chaos_cex_present = self.observation_table.chaos_counterexample(self.hypothesis)

            if not chaos_cex_present:
                if self.automaton_type == 'mdp':
                    self.hypothesis.states.remove(next(state for state in self.hypothesis.states if state.output == 'chaos'))
                else:
                    self.hypothesis.states.remove(next(state for state in self.hypothesis.states if state.state_id == 'chaos'))

            if print_level > 1:
                print(f'Hypothesis: {learning_rounds}: {len(self.hypothesis.states)} states.')

            if print_level == 3:
                print_observation_table(self.observation_table, 'stochastic')

            cex = None

            if not chaos_cex_present:
                eq_query_start = time.time()
                cex = self.stochastic_teacher.equivalence_query(self.hypothesis)

                eq_query_time += time.time() - eq_query_start

            if cex:
                if print_level == 3:
                    print('Counterexample', cex)
                # get all prefixes and add them to the S set
                if self.cex_processing is None:
                    for pre in get_cex_prefixes(cex, self.automaton_type):
                        if pre not in self.observation_table.S:
                            self.observation_table.S.append(pre)
                else:
                    suffixes = None
                    if self.cex_processing == 'longest_prefix':
                        prefixes = self.observation_table.S + list(self.observation_table.get_extended_s())
                        suffixes = stochastic_longest_prefix(cex, prefixes)
                    elif self.cex_processing == 'rs':
                        suffixes = stochastic_rs(sul, cex, self.hypothesis)
                    for suf in suffixes:
                        if suf not in self.observation_table.E:
                            self.observation_table.E.append(suf)
                            break

            # Ask queries for non-completed cells and update the observation table
            refined = self.observation_table.refine_not_completed_cells(self.n_resample)
            self.observation_table.update_obs_table_with_freq_obs()

            if self.property_based_stopping and learning_rounds >= min_rounds:
                # stop based on maximum allowed error
                if stop_based_on_confidence(self.hypothesis, self.property_based_stopping, print_level):
                    break
            else:
                # stop based on number of unambiguous rows
                stop_based_on_unambiguity = self.observation_table.stop(learning_rounds, chaos_cex_present, cex,
                                                                   self.stopping_range_dict,
                                                                   target_unambiguity=self.target_unambiguity,
                                                                   min_rounds=min_rounds, max_rounds=max_rounds,
                                                                   print_unambiguity=print_level > 1)
                if stop_based_on_unambiguity:
                    break

            if not refined:
                break

        total_time = round(time.time() - start_time, 2)
        eq_query_time = round(eq_query_time, 2)
        learning_time = round(total_time - eq_query_time, 2)

        info = {
            'learning_rounds': learning_rounds,
            'automaton_size': len(self.hypothesis.states),
            'queries_learning': self.stochastic_teacher.sul.stats.num_queries - self.eq_oracle.num_queries,
            'steps_learning': self.eq_oracle.num_queries,
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

        return self.hypothesis
