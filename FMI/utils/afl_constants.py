INSTR_AFL_MAP_SIZE_POW2 = 16
INSTR_AFL_MAP_SIZE = 1 << INSTR_AFL_MAP_SIZE_POW2

# Extra-large blocks, selected very rarely (<5% of the time): */
AFL_HAVOC_BLK_XL = 32768
# Caps on block sizes
AFL_HAVOC_BLK_SMALL = 32
AFL_HAVOC_BLK_MEDIUM = 128
AFL_HAVOC_BLK_LARGE = 1500

AFL_ARITH_MAX = 35
AFL_HAVOC_STACK_POW2 = 7
SPLICE_CYCLES = 15
AFL_HAVOC_CYCLES = 256
AFL_HAVOC_MAX_MULT = 16
AFL_SPLICE_HAVOC = 32
AFL_THIRD_CASE_CONST = 10

interesting_8_Bit = [128, 255, 0, 1, 16, 32, 64, 100, 127]
interesting_16_Bit = [65535, 32897, 128, 255, 256, 512, 1000, 1024, 4096, 32767]
interesting_32_Bit = [4294967295, 2248146693, 2147516417, 32768, 65535, 65536, 100663045, 2147483647]

INSTR_AFL_ENV = "__AFL_SHM_ID"

SHM_OVERWRITE = ""
SHM_POSIX = False
AFL_WITHOUT_FORKSERVER = 'afl_fork'
AFL_FORKSERVER = 'afl_fork_server'
