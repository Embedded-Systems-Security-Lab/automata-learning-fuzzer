from threading import Thread
import os

from FMI.utils.decorators import FMILogger
from FMI.SML.inf.SULs.automata_sul import ICSProtocolSUL
from FMI.SML.inf.base.sul import CacheSUL, NonDeterministicSULWrapper
from FMI.SML.inf.learning_algs import LStar, NDLStar, StochasticLStar
from FMI.SML.inf.oracles import RandomWordEqOracle, RandomWalkEqOracle
from FMI.SML.inf.utils import visualize_automaton, save_automaton_to_file

from FMI.network.tcp_socket_connection import TCPSocketConnection
from FMI.SML.RPE.rpe import RPE
from FMI.format_learner.abstraction import AbstractionLayer
from FMI.network.network_process_wrapper import NetworkProcessWrapper, NetworkProcessWrapperMaker
from FMI.SML.inf.base.sul import CacheSUL
from FMI.utils.time import Timer
from FMI.utils import exception
from FMI.SML.inf.utils import save_automaton_to_file, load_automaton_from_file

g_automata_method = { 'det': 'mealy', 'non_det': 'onfsm','stoch': 'smm'}

@FMILogger
class ActiveGrammarInferer():

    def __init__(self, alphabet, process_wrapper, channel, abstraction_layer, project, cache_buffer_size=10, visualize_automata=True,
                output_automata_full_path='learned_model', num_walks=20, min_walk_len=5, max_walk_len=10,
                reset_after_cex=True, automata_method='stoch', oracle_method='walk'):
        self.abstraction_layer = abstraction_layer
        self.channel = channel
        self.process_wrapper = process_wrapper
        # self.session = session
        self.cache_buffer_size = cache_buffer_size
        self.visualize_automata = visualize_automata
        self.output_automata_full_path = output_automata_full_path
        self.sul = ICSProtocolSUL(self.channel, self.process_wrapper, self.abstraction_layer, project)
        self.alphabet = self.sul.alphabet
        if oracle_method == 'word':
            self.eq_oracle = RandomWordEqOracle(self.alphabet, self.sul, num_walks=num_walks, min_walk_len=min_walk_len, max_walk_len=max_walk_len, reset_after_cex=reset_after_cex)
        elif oracle_method == 'walk':
            self.eq_oracle = RandomWalkEqOracle(self.alphabet, sul=self.sul, num_steps=100, reset_prob=0.11, reset_after_cex=reset_after_cex)
        else:
            raise Exception("Unknown method")
        if automata_method == 'stoch':
            self.lstar = StochasticLStar(self.alphabet, self.sul, self.eq_oracle, automaton_type='smm', n_resample=1000, strategy='normal', cex_processing=None)
        elif automata_method == 'det':
            self.cache_sul = CacheSUL(self.sul)
            self.lstar = LStar(self.alphabet, self.cache_sul, eq_oracle=self.eq_oracle)
        elif automata_method == 'non_det':
            self.cache_sul = NonDeterministicSULWrapper(self.sul)
            self.lstar = NDLStar(self.alphabet, self.cache_sul, eq_oracle=self.eq_oracle)
        else:
            raise Exception("Unknown learning automata method")
        self.learned_model = None
        self.automata_method = automata_method


    def learn(self):
        self._logger.info("Configuring the inference process")
        self._logger.info('Starting the learning algorithm')
        with Timer() as t:
            try:
                self.learned_model, _ = self.lstar.run(print_level=1)
            except exception.FMIRuntimeError as e:
                print(f"Got the following errors {e}")
            finally:
                self.process_wrapper.kill()
            self.time_elapsed = t.elapsed_time()
        #print(self.cache_sul.sul.cov)
        self._logger.info('The learning algorithm took: {}s'.format(self.time_elapsed))
        return self.learned_model

    def save_model(self, file_path):
        if self.learned_model is None:
            raise Exception
        save_automaton_to_file(self.learned_model, file_path)

    def load_model(self, file_path):
        if self.automata_method not in g_automata_method:
            raise Exception('Automata type not supported')

        self.learned_model = load_automaton_from_file(file_path, g_automata_method[self.automata_method])
        #print(self.learned_model)

    def visualize_automaton(self):
        if self.learned_model:
            visualize_automaton(self.learned_model)

    def get_states_transition_sequence(self):
        if self.learned_model is None:
            try:
                self.learned_model = self.lstar.get_hypothesis()
            except:
                raise Exception
        self.transitions = {self.learned_model.initial_state.state_id: None}
        for state in self.learned_model.states:
            if state is not self.learned_model.initial_state:
                self.transitions[state.state_id] = self.learned_model.get_shortest_path(self.learned_model.initial_state, state)
        return self.transitions

