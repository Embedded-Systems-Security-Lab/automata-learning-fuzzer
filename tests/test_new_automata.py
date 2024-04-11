import sys
import argparse
import os


from FMI.network.tcp_socket_connection import TCPSocketConnection
from FMI.SML.RPE.rpe import RPE
from FMI.format_learner.abstraction import AbstractionLayer
from FMI.active_grammar_inferer import ActiveGrammarInferer
from FMI.restarters.afl_folk_restarter import AFLForkRestarter
from FMI.SML.inf.utils import visualize_automaton

parser = argparse.ArgumentParser()
parser.add_argument("--data", type=str, help="CSV file to reverse engineer",
    default="/home/uchenna/GODS_PLAN_BREAKTHROUGH_EPICS/Resources/CODE/fuzzing-protocol-reverse-engineering/FMI/data/modbus/modbusSmall.pcap")
parser.add_argument("--folder", type=str, help="CSV file to reverse engineer",
    default="/home/uchenna/GODS_PLAN_BREAKTHROUGH_EPICS/Resources/CODE/fuzzing-protocol-reverse-engineering/FMI/data/IEC104")
args = parser.parse_args()
server_path = "./3rd_party_protocol/epics_project/support/pvxs/example/O.linux-x86_64/mailbox test"
data1 = "./FMI/data/epics/pvxs/mailbox/mailbox_test_src_to_dst.pcap"

message = RPE.process_one_file(data1)
rpe = RPE()
sym = rpe.get_symbols(message)
num_alph = 3
val = list(sym.values())[2:num_alph+2]

abslayer = AbstractionLayer(val)
uut = TCPSocketConnection(host="localhost", port=5075)
n = AFLForkRestarter(server_path)
alphabet = [s.name for s in sym.values()]
alphabet = alphabet[2:num_alph+2]


automata_learner = ActiveGrammarInferer(alphabet, n, uut, abslayer, deterministic=True)
try:
    learned_model = automata_learner.learn()
    visualize_automaton(learned_model)
    print("Finished")
except Exception as e:
    print(e)
finally:
    n.kill()
print("Done ")
