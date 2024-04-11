import time
import psutil

from FMI.SML.inf.base import SUL, CacheSUL
from FMI.SML.inf.automata import MealyMachine, Mdp
from FMI.network.network_process_wrapper import NetworkProcessWrapperMaker
from FMI.utils.decorators import FMILogger
from FMI.utils.constants import ERR_CONN_TIMEOUT
from FMI import shm
from FMI.utils.afl_constants import INSTR_AFL_ENV
from FMI.utils import helper, exception
from netzob.Model.Vocabulary.UnknownSymbol import UnknownSymbol
from FMI.utils.coverage_log import CoverageReport


class MealySUL(SUL):

    def __init__(self,mm):
        super(MealySUL,self).__init__()
        self.mm = mm

    def pre(self):
        self.mm.reset_to_initial()

    def post(self):
        pass

    def step(self, letter):
        return self.mm.step(letter)

class MdpSUL(SUL):
    def __init__(self, mdp: Mdp):
        super().__init__()
        self.mdp = mdp

    def query(self, word: tuple) -> list:
        initial_output = self.pre()
        out = [initial_output]
        for letter in word:
            out.append(self.step(letter))
        self.post()
        return out

    def pre(self):
        self.mdp.reset_to_initial()
        return self.mdp.current_state.output

    def post(self):
        pass

    def step(self, letter):
        return self.mdp.step(letter)

@FMILogger
class ICSProtocolSUL(SUL):
    def __init__(self, channel, process_wrapper, abstraction_layer, project):
        super(ICSProtocolSUL,self).__init__()
        self.channel = channel
        self.symbol_mapper = {}
        self.process_wrapper = process_wrapper
        self.abstraction_layer = abstraction_layer
        self.project = project
        self.initialize_dict()
        self._cov = None
        self.cov_count = 0
        self.connection_error_counter = 0
        self.unique_msg = dict()
        self.update_freq = 100
        self.log_cov_count = 0
        self.row_data = list()
        self.learning_round = 0

    def initialize_dict(self):
        for sym in self.abstraction_layer.symbols:

            if len(self.abstraction_layer.symbols[sym]) > 1:
                count = 0
                unique_msg = set()
                for msg in self.abstraction_layer.symbols[sym]:
                    self.pre()
                    try:
                        self.channel.send(msg)
                    except:
                        print('Could not send message')
                        continue
                    try:
                        recv_data = self.channel.recv()
                    except:
                        recv_data = b''
                    if recv_data != b'' and msg not in unique_msg:
                        #print('Found one: {} - {} - {}'.format(msg, recv_data, sym.name))
                        alph_name = ''.join([sym.name, str(count)])
                        self.symbol_mapper[alph_name] = msg
                        count += 1
                        unique_msg.add(msg)
                if count == 0:
                    self.symbol_mapper[sym.name] = next(iter(self.abstraction_layer.symbols[sym]))
            else:
                self.symbol_mapper[sym.name] = next(iter(self.abstraction_layer.symbols[sym]))
        self.alphabet = list(self.symbol_mapper.keys())

    def get_raw_ics_message(self, letter):
        return self.symbol_mapper[letter]

    def update_learning_round(self, learning_round):
        self.learning_round = learning_round

    def step(self, letter):
        if letter is not None and letter not in self.symbol_mapper:
            print(letter)
            print(self.symbol_mapper)
            raise Exception("Letter not in Learning algorithm")
        elif letter in self.symbol_mapper:
            msg_out = self.symbol_mapper[letter]
        try:
            # print("Sending: {} - {}".format(letter, msg_out))
            self.channel.send(msg_out)
        except:
            return b''
        try:
            recv_data = self.channel.recv()
        except:
            recv_data = b''
        # print("receiving: {}".format(recv_data))
        return recv_data

    def pre(self,time_out=(0.000001, 0.04)):
        """This restarts the server, might need to close and open connection"""
        self.process_wrapper.restart(planned=True)
        time.sleep(time_out[0])
        try:
            self.channel.open()
        except (exception.FMITargetConnectionFailedError, Exception):
            for _ in range(3):
                self.process_wrapper.restart(planned=True)
                print("Trying to restart")
                time.sleep(time_out[1])
                try:
                    self.channel.open()
                    break
                except Exception as e:
                    pass
    # Using shared memory for testing something
    def post(self):
        self.log_cov_count += 1
        mem = shm.get()
        mem.acquire()
        new_count = mem.directed_branch_coverage()
        if new_count > self.cov_count:
            self.cov_count = new_count
            self._cov = mem.buf
        mem.release()
        row = {"timestamp" : time.time(),"iteration": str(self.learning_round),"reported_coverage":new_count,
                "unique_crashes": "-", "total_crashes": "-", "phase": "learning", "avg_exec": "-"}
        self.row_data.append(row)
        if self.log_cov_count % self.update_freq == 0:
            self.log_coverage_info()
        self.channel.close()


    @property
    def cov(self):
        return self._cov

    def log_coverage_info(self):
        CoverageReport.update_file(self.project.coverage_csv, self.row_data)
        self.row_data = list()
        self.log_cov_count = 0








