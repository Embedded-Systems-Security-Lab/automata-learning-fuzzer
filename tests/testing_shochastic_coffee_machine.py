import sys
import argparse
import os

from FMI.SML.inf.learning_algs import StochasticLStar
from FMI.SML.inf.oracles import RandomWalkEqOracle
from FMI.network.tcp_socket_connection import TCPSocketConnection
from FMI.SML.RPE.rpe import RPE
from FMI.format_learner.abstraction import AbstractionLayer
from FMI.active_grammar_inferer import ActiveGrammarInferer
from FMI.restarters.afl_fork_restarter import AFLForkRestarter
from FMI.SML.inf.utils import visualize_automaton
from FMI.SML.inf.SULs.automata_sul import ICSProtocolSUL

parser = argparse.ArgumentParser()
parser.add_argument("--data", type=str, help="CSV file to reverse engineer",
    default="/home/uchenna/GODS_PLAN_BREAKTHROUGH_EPICS/Resources/CODE/fuzzing-protocol-reverse-engineering/FMI/data/modbus/modbusSmall.pcap")
parser.add_argument("--folder", type=str, help="CSV file to reverse engineer",
    default="/home/uchenna/GODS_PLAN_BREAKTHROUGH_EPICS/Resources/CODE/fuzzing-protocol-reverse-engineering/FMI/data/IEC104")
args = parser.parse_args()

server_path = "./3rd_party_protocol/epics_project/support/pvxs/example/O.linux-x86_64/mailbox test"
data1 = "./FMI/data/epics/pvxs/mailbox/mailbox_test_src_to_dst.pcap"

# server_path = "./3rd_party_protocol/lava/lib60870-C-2.2/src/server_taint_analysis 3105"
# data1 = "./combined.pcap"

message = RPE.process_one_file(data1)

rpe = RPE()
sym = rpe.get_symbols(message)
num_alph = 2
val = list(sym.values())[:num_alph]

alphabet = [s.name for s in sym.values()]
alphabet = alphabet[:num_alph]

model_path = 'smm_pvxs'

abslayer = AbstractionLayer(val)

uut = TCPSocketConnection(host="localhost", port=5075)
# n = NetworkProcessWrapperMaker(server_path, listen_ip="localhost", listen_port=5075, name="IEC_61850 server", restart_process=True)
n = AFLForkRestarter(server_path)
sul = ICSProtocolSUL(uut, n, abslayer)
print("Got here 2")
eq_oracle = RandomWalkEqOracle(alphabet, sul=sul, num_steps=1000, reset_prob=0.11,
                                           reset_after_cex=True)
#learned_mdp = StochasticLStar(alphabet, sul, eq_oracle, n_c=20, n_resample=500, strategy='classic', cex_processing=None)
learned_mdp = ActiveGrammarInferer(alphabet,  n, uut, abslayer)
#automata_learner = ActiveGrammarInferer(alphabet, n, uut, abslayer, deterministic=False)

model = 'smm_pvxs.dot'
if os.path.exists(model):
    learned_mdp.load_model(model)
    learned_mdp.get_states_transition_sequence()
else:
    print('Nothing found')
print("Got here 2")
exit()
try:
    model= learned_mdp.learn()
    print(model)
    learned_mdp.save_model(model_path)
    visualize_automaton(model)
    print(model.initial_state)
except Exception as e:
    print(e)
finally:
    n.kill()
print("Done ")

























# from FMI.SML.inf.SULs import MdpSUL
# from FMI.SML.inf.learning_algs import StochasticLStar
# from FMI.SML.inf.oracles import RandomWalkEqOracle
# from FMI.SML.inf.utils import get_faulty_coffee_machine_MDP

# mdp = get_faulty_coffee_machine_MDP()
# # print(mdp)

# input_alphabet = mdp.get_input_alphabet()
# print(input_alphabet)

# sul = MdpSUL(mdp)
# eq_oracle = RandomWalkEqOracle(input_alphabet, sul=sul, num_steps=1000, reset_prob=0.11,
#                                            reset_after_cex=True)
# learned_mdp = StochasticLStar(input_alphabet, sul, eq_oracle, automaton_type='smm', n_resample=500, strategy='normal', cex_processing=None)
# model, _ = learned_mdp.run(min_rounds=10,max_rounds=50,print_level=3)

# # un_stochastic_Lstar(input_alphabet, sul, eq_oracle, automaton_type='smm', strategy='normal', min_rounds=10,
# # #                                    max_rounds=50, cex_processing=None, print_level=3)
