from FMI.mutation.base_mutation import Mutation
from FMI.utils.afl_constants import AFL_ARITH_MAX, AFL_HAVOC_BLK_XL, AFL_HAVOC_STACK_POW2, SPLICE_CYCLES, AFL_SPLICE_HAVOC, AFL_HAVOC_CYCLES
from FMI.utils import afl_constants
from FMI.utils import helper
from FMI.utils.decorators import FMILogger
import random
import copy
"""
Credit:
https://github.com/mxmssh/manul/blob/master/afl_fuzz.py

"""
# AFL_ARITH_MAX = 35

class AFL_MUTATION(object):

    BITS_FLIP = {1:(0x80, 8), 2: (0xC0, 7), 4: (0xF0, 5)} #Corresponfding to 1, 2, 4 bits
    BYTE_FLIP = {1:0, 2: 1, 4: 3}
    BYTE_ARITH = {1:(0,None, helper.store_8), 2:(2,helper.load_16,helper.store_16), 4:(4,helper.load_32,helper.store_32)}
    BYTE_ARITH_INTERESTING = {1:(0, 0, afl_constants.interesting_8_Bit, helper.in_range_8, None, helper.store_8),
                                2:(2, 1, afl_constants.interesting_16_Bit, helper.in_range_16, helper.swap_16, helper.store_16),
                                4:(4, 3, afl_constants.interesting_32_Bit, helper.in_range_32, helper.swap_32, helper.store_32)}

    def __init__(self,seed=None, tokens_list=list(), splice_files=set()):
        super(AFL_MUTATION, self).__init__()
        self.tokens_list = tokens_list
        self.splice_files = splice_files
        self.seed = seed
        if seed:
            random.seed(self.seed)
        self.update_func_to_choose()
        # print(type(self.splice_files))
        # exit()

    def update_func_to_choose(self):
        func_to_choose_from = {0 : self.havoc_bitflip, 1 :self.havoc_interesting_byte, 2 :self.havoc_interesting_byte, 3 :self.havoc_interesting_byte,
                      4: self.havoc_randomly_add_or_substract, 5: self.havoc_randomly_add_or_substract, 6: self.havoc_randomly_add_or_substract,
                      7: self.havoc_randomly_add_or_substract, 8: self.havoc_randomly_add_or_substract, 9: self.havoc_randomly_add_or_substract,
                      10: self.havoc_set_randomly, 11: self.havoc_remove_randomly_block, 12: self.havoc_clone_randomly_block,
                      13: self.havoc_overwrite_randomly_block}

        if self.tokens_list:
            func_to_choose_from.update({14: self.havoc_overwrite_or_insert_with_dict, 15: self.havoc_overwrite_or_insert_with_dict})
        self.func_to_choose_from = func_to_choose_from

    ###############################################################
    #################### Deterministic Stage ######################
    ###############################################################

    def bit_flip(self, data, pos, num_bits):
        if num_bits not in AFL_MUTATION.BITS_FLIP:
            return data
        if not isinstance(data,bytearray):
            print("didn't get the right data type")
            return data
        if pos is None:
            pos = 0
        if pos >= len(data)*AFL_MUTATION.BITS_FLIP[num_bits][1]:
            return data
        data[int(pos/AFL_MUTATION.BITS_FLIP[num_bits][1])] ^= (AFL_MUTATION.BITS_FLIP[num_bits][0] >> (pos % AFL_MUTATION.BITS_FLIP[num_bits][1]))
        return data

    def byte_flip(self,data,pos, num_bytes):
        if num_bytes not in AFL_MUTATION.BYTE_FLIP:
            return data
        if not isinstance(data,bytearray):
            print("didn't get the right data type")
            return
        if pos is None:
            pos = 0

        if pos + AFL_MUTATION.BYTE_FLIP.get(num_bytes,0) >= len(data):
            return data
        if len(data) > AFL_MUTATION.BYTE_FLIP.get(num_bytes,0):
            data[pos] ^= 0xFF
            if num_bytes > 1:
                data[pos + 1] ^= 0xFF
            if num_bytes >=4:
                data[pos + 2] ^= 0xFF
                data[pos + 3] ^= 0xFF
        return data

    def mutate_byte_arithematic(self, data, pos_list, num_bytes):
        data_len = len(data)
        if num_bytes not in AFL_MUTATION.BYTE_ARITH or data_len < AFL_MUTATION.BYTE_ARITH[num_bytes][0]:
            return data
        if not pos_list:
            pos_list = [0, 0, False]

        if pos_list[1] > AFL_ARITH_MAX:
            pos_list[0] += 1
            pos_list[1] = 0

        if pos_list[0] + AFL_MUTATION.BYTE_FLIP.get(num_bytes,0) >= len(data):
            if pos_list[2] == False:
                pos_list = [0, 0, True]
            else:
                return data
        if AFL_MUTATION.BYTE_ARITH[num_bytes][1]:
            val = AFL_MUTATION.BYTE_ARITH[num_bytes][1](data, pos_list[0])
        else:
            val = data[pos_list[0]]
        if pos_list[2] == False:
            val += pos_list[1]
        else:
            val -= pos_list[1]

        AFL_MUTATION.BYTE_ARITH[num_bytes][2](data, pos_list[0], val)

        return data

    def mutate_byte_interesting(self, data, pos_list, num_bytes):
        data_len = len(data)
        if num_bytes not in AFL_MUTATION.BYTE_ARITH_INTERESTING or data_len < AFL_MUTATION.BYTE_ARITH_INTERESTING[num_bytes][0]:
            return data
        values = AFL_MUTATION.BYTE_ARITH_INTERESTING[num_bytes]

        if not pos_list:
            pos_list = [0, 0, False]

        if pos_list[1] >= len(values[2]):
            pos_list[0] += 1
            pos_list[1] = 0

        if pos_list[0] + values[1] >= data_len:
            if pos_list[2] == False:
                pos_list = [0, 0, True]
            else:
                return data
        interesting_value = values[3](values[2][pos_list[1]])
        if pos_list[2] and values[4]:
            interesting_value = values[4](interesting_value)

        values[5](data, pos_list[0], interesting_value)

        return data

    ###############################################################
    #################### Non-deterministic Stage ##################
    ###############################################################

    def dictionary_overwrite(self, data, pos_list: list):
        tokens_len = len(self.tokens_list)
        if tokens_len <= 0 or pos_list[0] >= tokens_len: return data
        if not pos_list: pos_list = [0, 0]
        data_len = len(data)
        token = self.tokens_list[pos_list[0]]
        place = pos_list[1]
        # if data_len < len(token):
        #     return data
        if place >= data_len:
            pos_list[0] += 1
            pos_list[1] = 0

            if pos_list[0] >= len(self.tokens_list):
                return data

        data = data[:place] + bytearray(token) + data[place + len(token):]

        return data

    def dictionary_insert(self, data, pos_list):
        if len(self.tokens_list) <= 0: return data
        if not pos_list: pos_list = [0, 0]
        data_len = len(data)
        token = self.tokens_list[pos_list[0]]
        place = pos_list[1]

        if place >= data_len:
            pos_list[0] += 1
            pos_list[1] = 0

            if pos_list[0] >= len(self.tokens_list):
                return data

        data = data[:place] + bytearray(token) + data[place:]

        return data

    def rand(self, value):
        return random.randint(0, value-1) if value else value

    # Only flip one bit
    def havoc_bitflip(self, data):
        value_to_flip = self.rand(len(data)*8)
        one_bit = 1
        data = self.bit_flip(data, value_to_flip, one_bit)
        return data

    def havoc_interesting_byte(self, data, num_bytes):
        data_len = len(data)
        if num_bytes not in AFL_MUTATION.BYTE_ARITH_INTERESTING or data_len < AFL_MUTATION.BYTE_ARITH_INTERESTING[num_bytes][0]:
            return data
        values = AFL_MUTATION.BYTE_ARITH_INTERESTING[num_bytes]
        value_to_change = self.rand(len(data)- values[1])
        one_bit = 1
        interesting_value_index = self.rand(len(values[2]))
        swap = self.rand(2)
        pos_list = [value_to_change,interesting_value_index, swap] # 3rd value is dummy value, does not matter
        data = self.mutate_byte_interesting(data, pos_list, num_bytes)
        return data

    def havoc_randomly_add_or_substract(self, data, num_bytes, is_add):
        data_len = len(data)
        if num_bytes not in AFL_MUTATION.BYTE_ARITH_INTERESTING or data_len < AFL_MUTATION.BYTE_ARITH_INTERESTING[num_bytes][0]:
            return data
        values = AFL_MUTATION.BYTE_ARITH_INTERESTING[num_bytes]
        pos_list = [self.rand(data_len - values[1]), self.rand(AFL_ARITH_MAX), is_add]
        data = self.mutate_byte_arithematic(data, pos_list, num_bytes)
        return data

    def havoc_set_randomly(self, data):
        pos = self.rand(len(data))
        max_pos = 255
        data[pos] = helper.in_range_8(data[pos] ^ (1 + self.rand(max_pos)))
        return data

    def havoc_remove_randomly_block(self, data):
        data_len = len(data)
        if data_len <= 2:
            return data
        len_to_remove = helper.AFL_choose_block_len(data_len - 1)
        pos = self.rand(data_len - len_to_remove + 1)
        data = data[:pos] + data[pos+len_to_remove:]
        return data

    def prepare_block(self, data):
        actually_clone = self.rand(4)
        data_len = len(data)

        if actually_clone:
            clone_len = helper.AFL_choose_block_len(data_len)
            clone_from = self.rand(data_len - clone_len + 1)
        else:
            clone_len = helper.AFL_choose_block_len(AFL_HAVOC_BLK_XL)
            clone_from = 0

        clone_to = self.rand(data_len)
        if actually_clone:
            block = data[clone_from:clone_from + clone_len]
        else:
            use_data_block = self.rand(2)
            if use_data_block:
                block_start = self.rand(data_len)
                block = data[block_start:block_start+clone_len]
            else:
                block = [self.rand(256)] * clone_len
                block = bytearray(block)

        return block, clone_to, clone_len

    def havoc_clone_randomly_block(self, data):
        block, clone_to, clone_len = self.prepare_block(data)
        if clone_len == 0: return data
        data = data[:clone_to] + block + data[clone_to:]
        return data

    def havoc_overwrite_randomly_block(self, data):
        block, clone_to, clone_len = self.prepare_block(data)
        if clone_len == 0: return data
        data = data[:clone_to] + block + data[clone_to+clone_len:]
        return data

    def havoc_overwrite_or_insert_with_dict(self, data, is_overwrite):
        pos_list = [self.rand(len(self.tokens_list)), self.rand(len(data))]
        if is_overwrite:
            data = self.dictionary_overwrite(data, pos_list)
        else:
            data = self.dictionary_insert(data, pos_list)
        return data

    def havoc(self, data, pos_list, max_havoc_cycles):
        if not pos_list: pos_list = 0
        if max_havoc_cycles != None and pos_list >= max_havoc_cycles: return data


        val = self.rand(AFL_HAVOC_STACK_POW2)
        use_stacking = 1 << val


        for i in range(use_stacking):
            method = self.rand(len(self.func_to_choose_from))
            #print(method, end=' ')
            if method == 1:
                data = self.func_to_choose_from[method](data, 1)
            elif method == 2:
                data = self.func_to_choose_from[method](data, 2)
            elif method == 3:
                data = self.func_to_choose_from[method](data, 4)
            elif method == 4:
                data = self.func_to_choose_from[method](data, 1, True)
            elif method == 5:
                data = self.func_to_choose_from[method](data, 1, False)
            elif method == 6:
                data = self.func_to_choose_from[method](data, 2, True)
            elif method == 7:
                data = self.func_to_choose_from[method](data, 2, False)
            elif method == 8:
                data = self.func_to_choose_from[method](data, 4, True)
            elif method == 9:
                data = self.func_to_choose_from[method](data, 4, False)
            elif method == 14:
                data = self.func_to_choose_from[method](data, True)
            elif method == 15:
                data = self.func_to_choose_from[method](data, False)
            else:
                data = self.func_to_choose_from[method](data) # method = 0

        return data

    def splice(self, data, pos_state, max_havoc_cycles):
        data_len = len(data)

        if not pos_state:
            pos_state = 0
        if pos_state > SPLICE_CYCLES or len(self.splice_files) <= 1 or data_len <= 2: return self.havoc(data, 0, max_havoc_cycles)
        original_data = random.sample(self.splice_files, 1)[0]
        target_data = bytearray(original_data)
        target_len = len(target_data)
        if target_len <= 2 or helper.is_bytearrays_equal(data, target_data):
            self.splice_files.remove(original_data)
            return self.havoc(data, 0, max_havoc_cycles)
        f_diff, l_diff = helper.locate_diffs(data, target_data, min(len(data), len(target_data)))
        if l_diff < 2 or f_diff == l_diff:
            self.splice_files.remove(original_data)
            return self.havoc(data, 0, max_havoc_cycles)

        split_last_byte = f_diff + self.rand(l_diff - f_diff)
        block = data[f_diff:f_diff+split_last_byte]
        data = target_data[:f_diff] + block + target_data[f_diff+split_last_byte:]
        data = self.havoc(data, 0, max_havoc_cycles)

        return data

    def get_havoc_cycles(self, exec_per_sec, perf_score, splice):
        havoc_div = 1
        if exec_per_sec < 20:
            havoc_div = 10
        elif exec_per_sec >= 20 and exec_per_sec < 50:
            havoc_div = 5
        elif exec_per_sec >= 50 and exec_per_sec < 100:
            havoc_div = 2

        if splice:
            stage_max = AFL_SPLICE_HAVOC * perf_score / havoc_div / 100;
        else:
            stage_max = AFL_HAVOC_CYCLES * perf_score / havoc_div / 100

        return stage_max, perf_score

@FMILogger
class MutationEingine(Mutation):

    def __init__(self, parent_data, seed=None, tokens_list=list(), max_havoc_cycles=None, splice_files=set(), skip_deterministic=True):
        super(MutationEingine, self).__init__(seed)
        self.mutator = AFL_MUTATION(seed, tokens_list, splice_files)
        self.parent_data = bytearray(parent_data)
        self.max_havoc_cycles = max_havoc_cycles
        self.skip_deterministic = skip_deterministic
        self.initialize_generator()


    def add_data_splice_file(self, data):
        self.mutator.splice_files.add(data)


    def initialize_generator(self):
        self.w_bit = self.walking_bit_flip()
        self.w_byte = self.walking_byte_flip()
        self.w_byte_arith = self.walking_byte_arithematic()
        self.w_byte_int = self.walking_byte_interesting()
        self.w_d_overwrite = self.walking_dictionary_overwrite()
        self.w_d_insert = self.walking_dictionary_insert()
        self.non_det = self.perform_nondeterministic()

    def walking_bit_flip(self):
        for num_bits in AFL_MUTATION.BITS_FLIP:
            r_limit = len(self.parent_data)*(8  - num_bits + 1)
            for i in range(r_limit):
                data = copy.copy(self.parent_data)
                yield bytes(self.mutator.bit_flip(data, i, num_bits))


    def walking_byte_flip(self):
        for num_bytes in AFL_MUTATION.BYTE_FLIP:
            r_limit = len(self.parent_data) - num_bytes + 1
            for i in range(r_limit):
                data = copy.copy(self.parent_data)
                yield bytes(self.mutator.byte_flip(data, i, num_bytes))

    def walking_byte_arithematic(self):
        for num_bytes in AFL_MUTATION.BYTE_FLIP:
            for add_or_sub in [True, False]:
                r_limit = len(self.parent_data) - num_bytes + 1
                for i in range(r_limit):
                    for j in range(1,AFL_ARITH_MAX+1):
                        data = copy.copy(self.parent_data)
                        yield bytes(self.mutator.mutate_byte_arithematic(data, [i, j, add_or_sub], num_bytes))

    def walking_byte_interesting(self):
        for num_bytes in AFL_MUTATION.BYTE_FLIP:
            for add_or_sub in [True, False]:
                r_limit = len(self.parent_data) - num_bytes + 1
                for i in range(r_limit):
                    for j in range(len(AFL_MUTATION.BYTE_ARITH_INTERESTING[num_bytes][2])):
                        data = copy.copy(self.parent_data)
                        yield bytes(self.mutator.mutate_byte_interesting(data, [i, j, add_or_sub], num_bytes))

    def walking_dictionary_overwrite(self):
        r_limit = len(self.mutator.tokens_list)
        for i in range(r_limit):
            for j in range(len(self.parent_data)):
                data = copy.copy(self.parent_data)
                yield bytes(self.mutator.dictionary_overwrite(data, [i, j]))

    def walking_dictionary_insert(self):
        r_limit = len(self.mutator.tokens_list)
        for i in range(r_limit):
            for j in range(len(self.parent_data)):
                data = copy.copy(self.parent_data)
                yield bytes(self.mutator.dictionary_insert(data, [i, j]))

    def perform_nondeterministic(self):
        while True:
            if len(self.mutator.splice_files) >= 2:
                try:
                    yield bytes(self.mutator.splice(copy.copy(self.parent_data), 0, self.max_havoc_cycles)) # The max hovoc cycle should be used to switch between splice and havoc
                except Exception:
                    self._logger.info("The following input - {} - has no further data".format(self.parent_data))
                    raise Exception("Splice not working") # Rethink this
            try:
                yield bytes(self.mutator.havoc(copy.copy(self.parent_data), 0, self.max_havoc_cycles)) # The max hovoc cycle should be used to switch between splice and havoc
            except Exception:
                self._logger.info("The following input - {} - has no further data".format(self.parent_data))
                raise Exception("Havoc not working") #TODO: Rethink this


    def get_mutated_payload(self, mut_input=None):

        if (not self.skip_deterministic):
            try:
                return next(self.w_bit)
            except StopIteration:
                self._logger.info("finished walking bit for {}".format(self.parent_data))

            try:
                return next(self.w_byte)
            except StopIteration:
                self._logger.info("finished walking bytes for {}".format(self.parent_data))

            try:
                return next(self.w_byte_arith)
            except StopIteration:
                self._logger.info("finished walking byte arithematic for {}".format(self.parent_data))

            try:
                return next(self.w_byte_int)
            except StopIteration:
                self._logger.info("finished walking byte interesting for {}".format(self.parent_data))

            if self.mutator.tokens_list:
                try:
                    return next(self.w_d_overwrite)
                except StopIteration:
                    self._logger.info("finished dictionary overwrite for {}".format(self.parent_data))

                try:
                    return next(self.w_d_insert)
                except StopIteration:
                    self._logger.info("finished dictionary insert for {}".format(self.parent_data))

        try:
            return next(self.non_det)
        except StopIteration:
            self._logger.info("finished non deterministic for {}".format(self.parent_data))
        return None

