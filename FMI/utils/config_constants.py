CONFIG_TEMPLATE = """
[fuzzer]
log_level       = 3              # 3=debug   2=info   1=warning
write_logfile   = true           # writes a .log file to the project directory
debug_mode      = false          # write additional debug logs
host            = "localhost"    # host on which the target process listens
port            = 7777           # port on which the target process listens
ssl             = false          # (only for TCP) wraps the TCP socket in a SSL context
udp             = false          # Use UDP instead of TCP
fuzz_in_process = false          # use in-process fuzzing instead of fuzzing over the network
recv_timeout    = 0.1
colored_output  = true           # use ANSI Escape Codes to color terminal output
max_payload_size= 0              # Maximum size for fuzz payloads in bytes. 0 = no limit.
#payload_filter  = "path/to/filter.py"   # Define a filter for the mutated payloads (written in Python 3)
                                         # The python file must contain the following function:
                                         # def payload_filter_function(payload):
                                         #     # do stuff. (payload is 'bytes' object)
                                         #     return modified_payload_or_None

[target]
process_name    = "myprocess"    # Process name of the target. Must be unique, otherwise use process_pid
#process_pid     = 1234          # Specifify the target process via process ID
function        = 0x123456       # Function for which the coverage will be traced
                                 # Can either be an absolute address (integer, e.g. 0x12345)
                                 # or a symbol name (string, e.g. "handleClient")
remote_frida    = false          # Connect to a "remote" frida server (needs ssh portforwarding of the
                                 # frida server port to localhost)
frida_port      = 27042          # port for the remote frida connection. frizzer will connect to localhost:$PORT

# 'modules' is a filter list. Coverage will be traced only for modules / shared
# libs which match one of the search terms in 'modules'. It is important that
# the filter matches at least one module!
modules = [
        "tests/simple_binary/test",
    ]

# Multiple targets are supported but you probably don't want this
# (only meant for load-balancing setups were multiple processes handle the network traffic)
#[target2]
#process_name    = "myprocess"
#function        = 0x123456
#remote_frida    = true
#frida_port      = 27042
#modules = [
#        "tests/simple_binary/test",
#    ]
"""


CORPUS_DIR = "corpus"
MODEL_DIR = "model"
CORPUS_TRASH_DIR = "corpus_trash"
CRASH_DIR = "crashes"
CRASH_DIR_UNIQUE = "unique"
SUSPECT_DIR = "suspects"
DEBUG_DIR = "debug"
CONFIG_FILE = "config"
STATE_FILE = "state"
COVERAGE = "coverage"
STD_OUT = "_stdout.log"
HISTORY = "history"
PROJECT_DEFAULT = "_project_default_logger.log"
FRIDA_SRCIPT = "instrumentation/frida/frida_script.js"
HISTORY_SESSION = "frida_fuzzer.history"
