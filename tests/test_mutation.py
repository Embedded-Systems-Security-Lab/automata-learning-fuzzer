from FMI.mutation.radamsa.radamsa_mutation import RamdamsaMutation
from FMI.mutation.afl_mutation_strategy import AFL_MUTATION, MutationEingine
import copy
AFL_ARITH_MAX = 35

def in_range_16(value):
    return value & 0xffff

def load_16(value, pos):
    a = value[pos] << 8
    b = value[pos+1] % 0xff
    print(a, b, value[pos], value[pos+1])
    exit()
    return a + b

def store_16(data, pos, value):
    value = in_range_16(value)
    data[pos]   = (value & 0xff00) >> 8
    data[pos+1] = (value & 0x00ff)

def mutate_2bytes_arithmetic(data, func_state):
    data_len = len(data)
    if data_len < 2:
        return data, None

    if not func_state:
        func_state = [0, 0, False]

    if func_state[1] > AFL_ARITH_MAX:
        func_state[0] += 1
        func_state[1] = 0

    if func_state[0] + 1 >= data_len:
        if func_state[2] == False:
            func_state = [0, 0, True]
        else:
            return data, None

    # TODO: we have to check for could_be_bitflip()
    val = load_16(data, func_state[0])

    if func_state[2] == False:
        val += func_state[1]
    else:
        val -= func_state[1]

    store_16(data, func_state[0], val)

    func_state[1] += 1

    return data, func_state

my_mutator = RamdamsaMutation(777)
mut_value = my_mutator.get_mutated_payload(b'Hello')

afl_mut = AFL_MUTATION(seed=7777)
original_1 = bytearray("AAAAAAAAA", "utf-8")
original = bytearray("USER#username\x00", "utf-8")
# val = copy.copy(original)
print(original)

# res = afl_mut.bit_flip(val, 0, 4)
def get_value():
    for j in [True, False]:
        for i in range(8):
            val = copy.copy(original)
            res = afl_mut.mutate_byte_interesting(val, [0, i, j], 4)
            yield bytes(res)
        print()
        #break

def get_0_10():
    for i in range(10):
        yield i

def get_10_19():
    for i in range(10,20):
        yield i

val = get_0_10()
val_1 = get_10_19()

while True:
    try:
        a = next(val)
        print(a)
    except:
        print("Finished the first")
        a = None

    try:
        a = next(val_1)
        print(a)
    except:
        print("Finished the second")
        a = None
    if a == None:
        break

# afl_mut = MutationEingine(original,7777)
# res = None
# count = 0
# max_count = 20000
# while True:
#     count += 1
#     res = afl_mut.get_mutated_payload()
#     if res and len(res) > 7:
#         if chr(res[6]) == 'c' or chr(res[6]) == 'C':
#             if chr(res[7]) == 'r' or chr(res[7]) == 'R':
#                 print("Got the crash")
#                 break
#         if res[7] == 'r' or res[7] == 'R':
#             print("Got r but failed c")
#     if res and len(res) > 6:
#         print(res, count, len(res), res[6])
#     if res is None or count >= max_count: break

# def get_one_two():
#     for i in range(3):
#         yield i

# def get_three_five():
#     for i in range(3,6):
#         yield i

# def get_six_nine():
#     for i in range(6,10):
#         yield i
# first = get_one_two()
# second = get_three_five()
# third = get_six_nine()
# print(first, second, third)
# # exit()
# def get_input():
#     try:
#         return next(first)
#     except StopIteration:
#         try:
#             return next(second)
#         except StopIteration:
#             try:
#                 return next(third)
#             except StopIteration:
#                 print("Finished implementation")
#                 return -1
# print(get_input())
# print(get_input())
# print(get_input())
# print(get_input())
# print(get_input())
# print(get_input())
# print(get_input())
# print(get_input())
# print(get_input())
# print(get_input())
# print(get_input())
# print(get_input())
# print(get_input())
