"""
Note: The server communicates through port 102
And currently using the localhost

"""

import sys
import argparse
import os

from FMI.SML.inf.SULs.automata_sul import ICSProtocolSUL
from FMI.SML.inf.base.sul import NonDeterministicSULWrapper
from FMI.SML.inf.learning_algs import LStar, NDLStar
from FMI.SML.inf.oracles import StatePrefixEqOracle, RandomWordEqOracle
from FMI.SML.inf.utils import visualize_automaton

from FMI.network.tcp_socket_connection import TCPSocketConnection
from FMI.SML.RPE.rpe import RPE
from FMI.format_learner.abstraction import AbstractionLayer
from FMI.network.network_process_wrapper import NetworkProcessWrapper, NetworkProcessWrapperMaker
from FMI.SML.inf.non_deterministic_cache import NonDetCacheSUL

parser = argparse.ArgumentParser()
parser.add_argument("--data", type=str, help="CSV file to reverse engineer",
    default="/home/uchenna/GODS_PLAN_BREAKTHROUGH_EPICS/Resources/CODE/fuzzing-protocol-reverse-engineering/FMI/data/modbus/modbusSmall.pcap")
parser.add_argument("--folder", type=str, help="CSV file to reverse engineer",
    default="/home/uchenna/GODS_PLAN_BREAKTHROUGH_EPICS/Resources/CODE/fuzzing-protocol-reverse-engineering/FMI/data/")
args = parser.parse_args()

server_path = "./3rd_party_protocol/libmodbus/tests/unit-test-server"
data1 = os.path.join(args.folder, "modbus/unit_test_modbus_.pcap")
message = RPE.process_one_file(data1)
sym = RPE.get_symbols(message)


print(sym)
print(len(sym))
exit()
num_alph = 10
val = list(sym.values())[:num_alph]

abslayer = AbstractionLayer(val)
uut = TCPSocketConnection(host="localhost", port=1502)
n = NetworkProcessWrapperMaker(server_path, listen_ip="localhost", listen_port=1502, name="example server", restart_process=True)
alphabet = [s.name for s in sym.values()]
alphabet = alphabet[:num_alph]
print(alphabet)
sul = ICSProtocolSUL(uut,n,abslayer)
cache_sul = NonDeterministicSULWrapper(sul)
eq_oracle = RandomWordEqOracle(alphabet, cache_sul, num_walks=10, min_walk_len=5, max_walk_len=10,
                                   reset_after_cex=True)
lstar = NDLStar(alphabet, cache_sul, eq_oracle)
try:
    learned_model, info = lstar.run(max_learning_rounds=10)
    visualize_automaton(learned_model)

except Exception as e:
    print(e)
finally:
    n.stop()
print("Done ")



