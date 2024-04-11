import random

from FMI.SML.inf.base import Oracle, SUL

class StatePrefixEqOracle(Oracle):

    def __init__(self, alphabet: list, sul: SUL, walks_per_state=10, walk_len=30, depth_first=False):

        super(StatePrefixEqOracle, self).__init__(alphabet, sul)

        self.walks_per_state = walks_per_state
        self.steps_per_walk = walk_len
        self.depth_first = depth_first

        self.freq_dict = dict()


    def find_cex(self, hypothesis):

        states_to_cover = []
        for state in hypothesis.states:
            if state.prefix is None:
                state.prefix = hypothesis.get_shortest_path(hypothesis.initial_state, state)
            if state.prefix not in self.freq_dict.keys():
                self.freq_dict[state.prefix] = 0

            states_to_cover.extend([state] * (self.walks_per_state - self.freq_dict[state.prefix]))

        if self.depth_first:
            # states_to_cover.extend([state]* (self.walks_per_state - self.freq_dict[state.prefix]))
            states_to_cover.sort(key=lambda x: len(x.prefix), reverse=True)
        else:
            random.shuffle(states_to_cover)

        for state in states_to_cover:
            self.freq_dict[state.prefix] = self.freq_dict[state.prefix] + 1

            self.reset_hyp_and_sul(hypothesis)

            prefix = state.prefix
            for p in prefix:
                hypothesis.step(p)
                self.sul.step(p)
                self.num_steps += 1

            suffix = ()

            for _ in range(self.steps_per_walk):
                suffix += (random.choice(self.alphabet),)

                out_sul = self.sul.step(suffix[-1])
                out_hyp = hypothesis.step(suffix[-1])
                self.num_steps += 1

                if out_sul != out_hyp:
                    self.sul.post()
                    return prefix + suffix

        return

class StatePrefixOracleNondet(StatePrefixEqOracle):
    MAX_CEX_ATTEMPTS = 5
    def __init__(self, alphabet: list, sul: SUL, walks_per_state=10, walk_len=30, depth_first=False):
        super().__init__(alphabet,sul,walks_per_state,walk_len,depth_first)
        self.reset_time = 0

    def repeat_query(self, hypothesis, input_sequence):
        non_det_attempts = 0
        while non_det_attempts < 10:
            self.reset_hyp_and_sul(hypothesis)
            cex_found_counter = 0
            for input in input_sequence:
                out_hyp = hypothesis.step(input)
                self.num_steps += 1
                out_sul = self.sul.step(input)
                if out_sul == "":
                    non_det_attempts += 1
                    break
                if out_sul != out_hyp:
                    cex_found_counter += 1
                    if cex_found_counter == self.MAX_CEX_ATTEMPTS:
                        return True
            if out_sul != "":
                return False
        return True

    def find_cex(self, hypothesis):
        states_to_cover = []
        for state in hypothesis.states:
            if state.prefix is None:
                state.prefix = hypothesis.get_shortest_path(hypothesis.initial_state, state)
            if state.prefix not in self.freq_dict.keys():
                self.freq_dict[state.prefix] = 0

            states_to_cover.extend([state] * (self.walks_per_state - self.freq_dict[state.prefix]))

        if self.depth_first:
            # states_to_cover.extend([state]* (self.walks_per_state - self.freq_dict[state.prefix]))
            states_to_cover.sort(key=lambda x: len(x.prefix), reverse=True)
        else:
            random.shuffle(states_to_cover)

        print(f'states to cover len: {len(states_to_cover)}')

        for state in states_to_cover:
            self.freq_dict[state.prefix] = self.freq_dict[state.prefix] + 1
            out_sul = ""
            non_det_attempts = 0
            error_counter = 0
            while out_sul == b'' and error_counter < 10 and non_det_attempts < 10:
                try:
                    self.reset_hyp_and_sul(hypothesis)
                    out_sul = ''
                    prefix = state.prefix
                    for p in prefix:
                        hypothesis.step(p)
                        out_sul = self.sul.step(p)
                        self.num_steps += 1
                        if out_sul == "":
                            break
                    if out_sul == "":
                        error_counter += 1
                        continue
                    print(f'performed prefix: {prefix}')
                    suffix = ()

                    for _ in range(self.steps_per_walk):
                        suffix += (random.choice(self.alphabet),)

                        out_sul = self.sul.step(suffix[-1])
                        if out_sul == "":
                            error_counter += 1
                            break
                        out_hyp = hypothesis.step(suffix[-1])
                        print("hyp: " + out_hyp)
                        self.num_steps += 1

                        if out_sul != out_hyp:
                            reproducable_cex = self.repeat_query(hypothesis, prefix + suffix)
                            if reproducable_cex:
                                print("we found a cex")
                                return prefix + suffix
                    print(f'performed query: {prefix + suffix}')

                except FMINonDeterministicError:
                    print("Non-deterministic error in conformance testing.")
                    non_det_attempts += 1

                except RepeatedNonDeterministicError:
                    non_det_attempts += 1
                    print("Repeated non-deterministic error in conformance testing.")
                    if non_det_attempts == 5:
                        print("Reached maximum attempts ")
                        raise

        return
