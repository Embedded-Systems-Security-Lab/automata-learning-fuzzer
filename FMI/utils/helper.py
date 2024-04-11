import os
import random
from .afl_constants import *
import string
import json
import pickle
import signal

"""Credit to Manual Code: Source: https://github.com/mxmssh/manul"""
critical_signals_nix = {signal.SIGQUIT, signal.SIGILL, signal.SIGTRAP, signal.SIGBUS, signal.SIGFPE, signal.SIGSEGV,
                              signal.SIGXCPU, signal.SIGXFSZ, signal.SIGSYS}


def AFL_choose_block_len(limit):
    """
        Random function that chooses variable block length
    """
    rlim = 3

    case_id = RAND(rlim)
    if case_id == 0:
        min_value = 1
        max_value = AFL_HAVOC_BLK_SMALL
    elif case_id == 1:
        min_value = AFL_HAVOC_BLK_SMALL
        max_value = AFL_HAVOC_BLK_MEDIUM
    else:
        case_id = RAND(AFL_THIRD_CASE_CONST)
        if case_id:
            min_value = AFL_HAVOC_BLK_MEDIUM
            max_value = AFL_HAVOC_BLK_LARGE
        else:
            min_value = AFL_HAVOC_BLK_LARGE
            max_value = AFL_HAVOC_BLK_XL

    if min_value >= limit:
        min_value = 1

    return min_value + RAND(min(max_value, limit) - min_value + 1)


def RAND(value):
    return random.randint(0, value-1) if value else value

def load_8(value, pos):
    return value[pos]

def load_16(value,pos):
    return (value[pos] << 8) + (value[pos+1] % 0xff)

def load_32(value, pos):
    return (value[pos] << 24) + (value[pos+1] << 16) + (value[pos+2] << 8) + (value[pos+3] % 0xff)

def store_8(data, pos, value):
    data[pos] = in_range_8(value)

def store_16(data, pos, value):
    value = in_range_16(value)
    data[pos]   = (value & 0xff00) >> 8
    data[pos+1] = (value & 0x00ff)

def store_32(data, pos, value):
    value = in_range_32(value)
    data[pos]   = (value & 0xff000000) >> 24
    data[pos+1] = (value & 0x00ff0000) >> 16
    data[pos+2] = (value & 0x0000ff00) >> 8
    data[pos+3] = (value & 0x000000ff)

def in_range_8(value):
    return value & 0xff


def in_range_16(value):
    return value & 0xffff


def in_range_32(value):
    return value & 0xffffffff

# def swap_8(value): #Does not swap
#     return value

def swap_16(value):
    return (((value & 0xff00) >> 8) +
            ((value & 0xff) << 8))


def swap_32(value):
    return ((value & 0x000000ff) << 24) + \
           ((value & 0x0000ff00) << 8) + \
           ((value & 0x00ff0000) >> 8) + \
           ((value & 0xff000000) >> 24)

def bytes_to_str_8(value):
    return chr((value & 0xff))


def bytes_to_str_16(value):
    return chr((value & 0xff00) >> 8) + \
           chr((value & 0x00ff))


def bytes_to_str_32(value):
    return chr((value & 0xff000000) >> 24) + \
           chr((value & 0x00ff0000) >> 16) + \
           chr((value & 0x0000ff00) >> 8) + \
           chr((value & 0x000000ff))


def to_string_16(value):
    return chr((value >> 8) & 0xff) + \
           chr(value & 0xff)


def to_string_32(value):
    return chr((value >> 24) & 0xff) + \
           chr((value >> 16) & 0xff) + \
           chr((value >> 8) & 0xff) + \
           chr(value & 0xff)

def is_not_bitflip(value):
    return True
    if value == 0:
        return False

    sh = 0
    while (value & 1) == 0:
        sh += 1
        value >>= 1

    if value == 1 or value == 3 or value == 15:
        return False

    if (sh & 7) != 0:
        return True

    if value == 0xff or value == 0xffff or value == 0xffffffff:
        return False

    return True


def is_not_arithmetic(value, new_value, num_bytes, set_arith_max=None):
    if value == new_value:
        return False

    if not set_arith_max:
        set_arith_max = AFL_ARITH_MAX

    diffs = 0
    ov = 0
    nv = 0
    for i in range(num_bytes):
        a = value >> (8 * i)
        b = new_value >> (8 * i)
        if a != b:
            diffs += 1
            ov = a
            nv = b

    if diffs == 1:
        if in_range_8(ov - nv) <= set_arith_max or in_range_8(nv-ov) <= set_arith_max:
            return False

    if num_bytes == 1:
        return True

    diffs = 0
    for i in range(num_bytes / 2):
        a = value >> (16 * i)
        b = new_value >> (16 * i)

        if a != b:
            diffs += 1
            ov = a
            nv = b

    if diffs == 1:
        if in_range_16(ov - nv) <= set_arith_max or in_range_16(nv - ov) <= set_arith_max:
            return False

        ov = swap_16(ov)
        nv = swap_16(nv)

        if in_range_16(ov - nv) <= set_arith_max or in_range_16(nv - ov) <= set_arith_max:
            return False

    if num_bytes == 4:
        if in_range_32(value - new_value) <= set_arith_max or in_range_32(new_value - value) <= set_arith_max:
            return False

        value = swap_32(value)
        new_value = swap_32(new_value)

        if in_range_32(value - new_value) <= set_arith_max or in_range_32(new_value - value) <= set_arith_max:
            return False

    return True


def is_not_interesting(value, new_value, num_bytes, le):
    if value == new_value:
        return False

    for i in range(num_bytes):
        for j in range(len(interesting_8_Bit)):
            tval = (value & ~(0xff << (i * 8))) | (interesting_8_Bit[j] << (i * 8))
            if new_value == tval:
                return False

    if num_bytes == 2 and not le:
        return True

    for i in range(num_bytes - 1):
        for j in range(len(interesting_16_Bit)):
            tval = (value & ~(0xffff << (i * 8)) | (interesting_16_Bit[j] << (i * 8)))
            #print(" -> " + str(value) + " - " + str(new_value) + " - " + str(tval))
            if new_value == tval:
                return False

            #if num_bytes > 2:
            tval = (value & ~(0xffff << (i * 8))) | (swap_16(interesting_16_Bit[j]) << (i * 8));
            if new_value == tval:
                return False

    if num_bytes == 4 and le:
        for j in range(len(interesting_32_Bit)):
            if new_value == interesting_32_Bit[j]:
                return False

    return True

def get_random_string(length: int, chars: [] = string.ascii_uppercase + string.ascii_lowercase) -> str:
    s = ''.join(random.choice([x for x in chars]) for _ in range(0, length))
    if constants.TRACE:
        print(f"rng_trace, get_random_string, 1, {s}", file=sys.stderr)
    return s
def save_sequence_of_data_to_file(data, file_path):
        if data is None or file_path is None:
            return False

        with open(file_path, "w") as f:
            json.dump(data, f)

        return True

def write_byte_to_file(data, file_path):
    if data is None or file_path is None:
        return False
    with open(file_path, "wb") as f:
        f.write(data)

def read_byte_from_file(file_path):
    if not os.path.exists(file_path):
        return None
    with open(file_path, "rb") as f:
        cov = f.read()
    return cov

def store_list(item_list, file_path):
    with open(file_path, 'wb') as fp:
        pickle.dump(item_list, fp)

def read_list(file_path):

    with open (file_path, 'rb') as fp:
        item_list = pickle.load(fp)
    return item_list

def is_bytearrays_equal(data_1, data_2):
    if not data_1 or not data_2 or len(data_1) != len(data_2): return False

    for i in range(len(data_1)):
        if data_1[i] != data_2[i]: return False

    return True

def locate_diffs(data_1, data_2, min_len):

    f_loc, l_loc = -1, -1
    for i in range(min_len):
        if data_1[i] != data_2[i]:
            if f_loc == -1: f_loc = i
        l_loc = i

    return f_loc, l_loc


#TODO: Might remove this
def _update_env(identifier: str) -> {}:
    """
    Copy and update parent environment by supplementing AFL instrumentation environment variable

    :param identifier: shared memory identifier
    :return: Updated copy of environment dict
    """
    environ = os.environ.copy()
    environ[INSTR_AFL_ENV] = str(identifier)
    return environ


