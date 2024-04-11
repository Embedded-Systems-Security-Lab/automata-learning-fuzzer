import argparse
import os


from FMI.SML.RPE.rpe import RPE
from FMI.format_learner.abstraction import AbstractionLayer

parser = argparse.ArgumentParser()
parser.add_argument("--data", type=str, help="CSV file to reverse engineer",
    default="/home/uchenna/GODS_PLAN_BREAKTHROUGH_EPICS/Resources/CODE/fuzzing-protocol-reverse-engineering/FMI/data/modbus/modbusSmall.pcap")
parser.add_argument("--folder", type=str, help="CSV file to reverse engineer",
    default="/home/uchenna/GODS_PLAN_BREAKTHROUGH_EPICS/Resources/CODE/fuzzing-protocol-reverse-engineering/FMI/data/anoy_data")
args = parser.parse_args()

data1 = os.path.join(args.folder, "fuzz_.pcap")
data1 = "./rtsp_.pcap"
message = RPE.process_one_file(data1)

rpe = RPE()
sym = rpe.get_symbols(message)
print(sym)


abslayer = AbstractionLayer(list(sym.values()))
for s in sym.values():
    msg = abslayer.convert_symbol_to_msg(s)
    print(msg)
    symbol = abslayer.convert_msg_to_symbol(msg)
    print(symbol)



