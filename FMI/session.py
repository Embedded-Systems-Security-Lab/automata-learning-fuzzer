import csv
import json
import os
import sys
import threading
import time
from numpy import random
import array
import zlib
import itertools

# from .utils import helpers
from . import shm
from FMI.utils import constants, afl_constants
from typing import Dict, Any, Tuple

from .testcase import TestCase
from FMI.utils.server_status import SUT_STATUS


from FMI.utils.decorators import FMILogger
from FMI.active_grammar_inferer import ActiveGrammarInferer
from FMI.mutation.base_mutation import Mutation
from FMI.mutation.afl_mutation_strategy import MutationEingine
from FMI.projects.project import Project
from FMI.targets.target import Target
from FMI.utils import exception
from FMI.restarters import IRestarter
from FMI.utils import helper
from queue import PriorityQueue
from collections import defaultdict
from FMI.utils.coverage_log import CoverageReport



class SessionOptions(object):

    def __init__(self, *args, **kwargs):
        self.__dict__.update(kwargs)

class SessionClock(object):
    def __init__(self, time_budget: float = 0.0):
        self._budget = time_budget
        self._execution_time = 0.0
        self._start = 0.0
        self._stop = 0.0
        self._running = False

    @property
    def exhausted(self):
        return self._budget > 0 >= self._budget - self._execution_time

    @property
    def execution_time(self):
        return self._execution_time

    @property
    def budget(self):
        return self._budget

    def start(self):
        if self._running:
            return
        self._start = time.time()
        self._running = True

    def reset(self):
        self._execution_time = 0.0
        self._start = 0.0
        self._stop = 0.0
        self._running = False

    def stop(self):
        if not self._running:
            return
        self._stop = time.time()
        self._execution_time += self._stop - self._start
        self._running = False

@FMILogger
class Session(object):

    def __init__(self,
                 restart_sleep_time: float = 2.0,
                 target: Target = None,
                 restarter: IRestarter = None,
                 fuzz_protocol: "IFuzzer" = None,
                 learner: ActiveGrammarInferer = None,
                 mutator: defaultdict(lambda: defaultdict(Mutation)) = None, #dict for the new implementation
                 project: Project = None,
                 seed: int = 0,
                 time_budget: float = 0.0,
                 post_relax: bool = True,
                 debug: bool = False,
                 output: str = "",
                 dump_shm: bool = False,
                 deterministic: bool = False,
                 ):
        super().__init__()
        self.opts = SessionOptions(
            restart_sleep_time=restart_sleep_time,
            # Transmission Options
            host=target.target_connection.host,
            port=target.target_connection.port,
            send_timeout=target.target_connection._send_timeout,
            recv_timeout=target.target_connection._recv_timeout,
            pcap=fuzz_protocol.pcap,
            seed=seed,
            time_budget=time_budget,
            post_relax=post_relax,
            debug=debug,
            output=output,
            dump_shm=dump_shm,
            deterministic=deterministic,
        )

        self.fuzz_protocol = fuzz_protocol

        self.target = target
        if target:
            try:
                self.add_target(target)
            except exception as e:
                raise
        self.restarter = restarter
        self.restarter.restart(planned=True)
        self.time_budget = SessionClock(time_budget)
        self.test_case_cnt = 0
        # Do I need an active test case, to be deciecded
        self.is_paused = False
        self.prompt = None
        self.project = project
        self.learner = learner
        self.mutator = mutator
        self.seed = seed
        self.project = project
        self.queue_per_state = defaultdict(set)
        self.scheduler = defaultdict(SessionClock)
        self.test_case_per_state = defaultdict(str)
        self.state_sequence = None
        self.time_budget_per_state = 50
        self.first_run = True
        self.prev_cov_history = 0
        self.crash_bits = None
        self.num_crashes = 0
        self.num_unique_crashes = 0
        self.crashes = defaultdict(set)
        self.new_msg_to_convert = defaultdict(list)
        self.relearning = True
        self.num_relearning = 0
        self.new_state_ids = 0
        self.fuzzing_alphabet = set()
        self.fuzzing_row_data = list()
        self.iter = 0
        self.update_freq = 20
        self.execution_num = defaultdict(lambda: defaultdict(int))
        self.total_exec = 0
        self.last_exec = 0
        self.avg_exec = 0
        self.last_ms = None
        self.curr_ms = 0
        self.fuzzing_start_time = 0



    def start(self):
        try:
            t = threading.Thread(target=self.run_all)
            t.start()
            t.join()
        except (KeyboardInterrupt, IOError, Exception) as e:
            print(e)
            try:
                self.restarter.kill()
                mem = shm.get()
                mem.close()
                mem.unlink()
            except:
                pass
            try:
                sys.exit(130)
            except SystemExit:
                os._exit(130)

    # TODO: think of a better architecture to
    def build_corpus_model_inference(self):
        self._logger.info("Initializing Corpus ...")
        model = [os.path.join(self.project.model_dir, x) for x in os.listdir(self.project.model_dir)]
        file = os.path.join(self.project.project_dir, "shm_data.txt")
        if not model or not os.path.exists(file):
            file_name = os.path.join(self.project.model_dir, "learned_model")
            self.learner.learn()
            helper.write_byte_to_file(self.learner.sul.cov, file)
            self.learner.save_model(file_name)
            self.prev_cov_history = self.learner.sul.cov_count
        else:
            #Assume only one dot file for now
            self.learner.load_model(model[0])
            self.mm = helper.read_byte_from_file(file)
            mem = shm.get()
            mem.acquire()
            self.prev_cov_history = mem.update_history(self.mm)
            mem.release()
        # print(self.prev_cov_history)
        self.state_sequence = self.learner.get_states_transition_sequence()
        for s in list(self.state_sequence):
            if self.state_sequence[s] == ():
                self.state_sequence.pop(s, None)
        corpus = [os.path.join(self.project.corpus_dir, x) for x in os.listdir(self.project.corpus_dir)]

        if not corpus:
            self._logger.info("Saving file to the folder")
            file_path = os.path.join(self.project.corpus_dir, self.project.get_file_name_with_time("corpus")+".json")
            helper.save_sequence_of_data_to_file(self.state_sequence, file_path)
            corpus = [os.path.join(self.project.corpus_dir, x) for x in os.listdir(self.project.corpus_dir)]
            corpus.sort()
        self.corpus = corpus

    def obtain_sequence(self, state):
        if not self.state_sequence[state]:
            return []
        return [self.learner.sul.get_raw_ics_message(letter) for letter in self.state_sequence[state]]

    def init_queue(self):
        if not self.state_sequence: return # TODO: Raise an error instead
        for sym in self.learner.abstraction_layer.symbols:
            self.fuzzing_alphabet = self.fuzzing_alphabet.union(self.learner.abstraction_layer.symbols[sym])
        #self.fuzzing_alphabet = set(itertools.islice(self.fuzzing_alphabet, 20))
        # print(set(self.fuzzing_alphabet))

        self.splice_files = set(self.fuzzing_alphabet)
        for s in self.state_sequence:
            for val in self.fuzzing_alphabet:
                self.mutator[s][val] = MutationEingine(val, self.opts.seed, splice_files=self.splice_files)
            self.test_case_per_state[s] = TestCase(s, self, self.obtain_sequence(s))
            self.scheduler[s] = SessionClock(self.time_budget_per_state)


    #TODO: Fix this latter
    def write_run_json(self):

        mem = shm.get()
        mem.acquire()

        data = {
            "general": {
                "fuzzer": self.fuzz_protocol.name,
                "time_budget": self.time_budget.budget,
                "random_seed": self.opts.seed,
                "output": self.result_dir,
                "debug": self.opts.debug,
                "dump_shm": self.opts.dump_shm,
                "deterministic": self.opts.deterministic,
                "shm_overwrite": afl_constants.SHM_OVERWRITE,
            },
            "target": {
                "exec_command": self.restarter.cmd,
                "protocol": self.target.target_connection.proto,
                "connection": f'{self.target.target_connection.host}:{self.target.target_connection.port}',
                "send_timeout": self.opts.send_timeout,
                "recv_timeout": self.opts.recv_timeout,
            },
            "instrumentation": {
                "mmap_id": mem.name,
                "injection_env": afl_constants.INSTR_AFL_ENV,
                "mem_size": mem.size / 1024,
            },
            #TODO: Add logging of learning parameters
        }
        mem.release()
        CoverageReport.write_run_parameters(self.run_json, data)


    def cont(self):
        self.time_budget.stop()
        if self.time_budget.exhausted:
            self.is_paused = True
        result = not (self.time_budget.exhausted or self.is_paused)
        if result:
            self.time_budget.start()
        return result

    def handle_state_timeout(self, time_budget: SessionClock):
        time_budget.stop()
        if time_budget.exhausted:
            time_budget.reset()
            return False
        time_budget.start()
        return True

    def check_and_update_new_path_crash_bit(self, compare_bits):
        if not self.crash_bits:
            self.crash_bits = compare_bits
            return True
        new_path = False
        for j in range(len(compare_bits)):
            if compare_bits[j] and (compare_bits[j] & ~self.crash_bits[j]):
                # old = hex(self.crash_bits[j])
                self.crash_bits[j] = self.crash_bits[j] | compare_bits[j]
                # print(hex(self.crash_bits[j]), hex(compare_bits[j]),old)
                new_path = True

        return new_path

    def efficient_model_refinement(self):
        self.num_relearning += 1
        for state in self.new_msg_to_convert:
            for msg in self.new_msg_to_convert[state]:
                new_id = "{}_{}".format(state,self.new_state_ids)
                self.new_state_ids += 1
                new_seq = list(self.test_case_per_state[state].sequence)
                new_seq.append(msg)
                test_case = TestCase(new_id, self, new_seq)
                res = test_case.run_seq()
                if res:
                    self.test_case_per_state[new_id] = test_case
                    for m in self.fuzzing_alphabet:
                        self.mutator[new_id][m] = MutationEingine(m, self.opts.seed, splice_files=self.splice_files)
                    self.mutator[new_id][msg] = MutationEingine(msg, self.opts.seed, splice_files=self.splice_files)
                    self.fuzzing_alphabet.add(msg)
                    self.scheduler[new_id] = SessionClock(self.time_budget_per_state)
                    for s in self.mutator:
                        if s != state and msg not in self.mutator[s]:
                            self.mutator[s][msg] = MutationEingine(msg, self.opts.seed, splice_files=self.splice_files)
                else:
                    file_path = os.path.join(self.project.suspect_dir, str(self.num_crashes))
                    self.project.write_array(new_seq, file_path)



    def remove_redundant_state(self):
        for state in list(self.scheduler):
            if self.execution_num[state]["total"] > 200 and self.execution_num[state]["exec"]/self.execution_num[state]["total"] < 0.001:
                print("Removing the following {}".format(state))
                try:
                    input_sequence = list(self.test_case_per_state[state].sequence)
                    del self.scheduler[state]
                    del self.mutator[state]
                    del self.test_case_per_state[state]
                    if state in self.new_msg_to_convert:
                        del self.new_msg_to_convert[state]
                    self.num_crashes += 1
                    file_path = os.path.join(self.project.suspect_dir, str(self.num_crashes))
                    self.project.write_array(input_sequence, file_path)
                except Exception as e:
                    print(e)

    def dry_run(self):
        for state in self.scheduler:
            self._logger.info("Running the following {} state for dry run of all the initial alphabets".format(state))
            for payload in self.fuzzing_alphabet:
                err, executed, crash_status = self.test_case_per_state[state].run(payload, is_rec=False)
                recent_cov, curr_buf = self.test_case_per_state[state].coverage_snapshot
                changed = recent_cov > self.prev_cov_history
                self.prev_cov_history = recent_cov if changed else self.prev_cov_history
                if crash_status != SUT_STATUS.NO_CRASH and executed:
                    self.num_crashes += 1
                    if payload in self.crashes[state]:
                        continue
                    else:
                        input_sequence = list(self.test_case_per_state[state].sequence)
                        input_sequence.append(payload)
                        self.crashes[state].add(payload)
                    #TODO: Hash this instead, it will be better for efficiency
                    if self.check_and_update_new_path_crash_bit(bytearray(curr_buf)):
                        self.num_unique_crashes += 1
                        file_path = os.path.join(self.project.unique_crash_dir, str(self.num_crashes))
                        self.project.write_array(input_sequence, file_path)
                    else:
                        file_path = os.path.join(self.project.crash_dir, str(self.num_crashes))
                        self.project.write_array(input_sequence, file_path)
            row = {"timestamp" : time.time(),"iteration": self.iter,"reported_coverage": self.prev_cov_history,
                    "unique_crashes": self.num_unique_crashes, "total_crashes": self.num_crashes, "phase": "dry run fuzzing"}
            self.fuzzing_row_data.append(row)
            if len(self.fuzzing_row_data) % self.update_freq == 0:
                CoverageReport.update_file(self.project.coverage_csv, self.fuzzing_row_data)
                self.fuzzing_row_data = list()
        if len(self.fuzzing_row_data) != 0:
            CoverageReport.update_file(self.project.coverage_csv, self.fuzzing_row_data)
            self.fuzzing_row_data = list()

    def run_with_schedule(self):
        for state in self.scheduler:
            self._logger.info("Running the following {} state".format(state))
            while self.handle_state_timeout(self.scheduler[state]):
                new_payloads = set()
                for payload in self.mutator[state]:
                    fuzz_pkt = self.mutator[state][payload].get_mutated_payload()
                    err, executed, crash_status = self.test_case_per_state[state].run(fuzz_pkt)
                    self.execution_num[state]["total"] += 1
                    if executed:
                        self.execution_num[state]["exec"] += 1
                    self.total_exec += 1

                    recent_cov, curr_buf = self.test_case_per_state[state].coverage_snapshot
                    changed = recent_cov > self.prev_cov_history
                    self.prev_cov_history = recent_cov if changed else self.prev_cov_history
                    if changed or crash_status == SUT_STATUS.CRASH_AFTER_SEND or crash_status == SUT_STATUS.DISCONNECTED:
                        if changed:
                            #print(recent_cov, payload, fuzz_pkt)
                            self.splice_files.add(fuzz_pkt)
                        if changed or crash_status == SUT_STATUS.DISCONNECTED:
                            if fuzz_pkt not in self.mutator[state]:
                                new_payloads.add(fuzz_pkt)
                                if crash_status == SUT_STATUS.NO_CRASH:
                                    self.new_msg_to_convert[state].append(fuzz_pkt)
                        if crash_status == SUT_STATUS.CRASH_AFTER_SEND and executed:
                            print(f"crashed {executed} {crash_status} {fuzz_pkt} {state}")
                            self.num_crashes += 1
                            if fuzz_pkt in self.crashes[state]:
                                continue
                            else:
                                input_sequence = list(self.test_case_per_state[state].sequence)
                                input_sequence.append(fuzz_pkt)
                                self.crashes[state].add(fuzz_pkt)
                            if self.check_and_update_new_path_crash_bit(bytearray(curr_buf)):
                                self.num_unique_crashes += 1
                                file_path = os.path.join(self.project.unique_crash_dir, str(self.num_crashes))
                                self.project.write_array(input_sequence, file_path)
                            else:
                                file_path = os.path.join(self.project.crash_dir, str(self.num_crashes))
                                self.project.write_array(input_sequence, file_path)
                for fuzz_pkt in new_payloads:
                    self.mutator[state][fuzz_pkt] = MutationEingine(fuzz_pkt, self.opts.seed, splice_files=self.splice_files)
                curr_ms = time.time()
                if (self.last_ms is None):
                    self.avg_exec = (self.total_exec)/(curr_ms - self.fuzzing_start_time)
                else:
                    self.avg_exec = (self.total_exec - self.last_exec)/(curr_ms - self.last_ms)

                self.last_ms = curr_ms
                self.last_exec = self.total_exec
                row = {"timestamp" : time.time(),"iteration": self.iter,"reported_coverage": self.prev_cov_history,
                    "unique_crashes": self.num_unique_crashes, "total_crashes": self.num_crashes, "phase": "fuzzing", "avg_exec": self.avg_exec}
                self.fuzzing_row_data.append(row)
                if len(self.fuzzing_row_data) % self.update_freq == 0:
                    CoverageReport.update_file(self.project.coverage_csv, self.fuzzing_row_data)
                    self.fuzzing_row_data = list()
        self.remove_redundant_state()


    def run_all(self):
        self.build_corpus_model_inference()
        self.init_queue()
        self.restarter.restart(planned=True)
        self.dry_run()
        self.fuzzing_start_time = time.time()
        while self.cont():
            self.iter += 1
            self.new_msg_to_convert = defaultdict(list)
            self.run_with_schedule()
            self.restarter.kill()
            if self.new_msg_to_convert and self.relearning: self.efficient_model_refinement()
        if self.fuzzing_row_data: CoverageReport.update_file(self.project.coverage_csv, self.fuzzing_row_data)


    def add_target(self, target: Target):
        self.target = target
