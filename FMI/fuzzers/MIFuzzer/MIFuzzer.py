from FMI.fuzzers.ifuzzer import IFuzzer
from FMI.utils.exception import FMIError
from FMI.SML.RPE.rpe import RPE
from FMI.session import Session
from collections import defaultdict

class MIFuzzer(IFuzzer):
    """
    MIFuzzer --> Model inference based fuzzer
    """
    symbols = None
    symbols_name = None
    name = "MIFuzzer"
    init_corpus = None
    pcap = None
    sym_per_msg = defaultdict(set)

    @staticmethod
    def initialize(*args, **kwargs):
        if 'name' in kwargs:
            MIFuzzer.name = kwargs['name']
        if 'pcap' not in kwargs:
            raise FMIError(" Pcap file must be passed in as an argument")
        MIFuzzer.pcap = kwargs['pcap']
        MIFuzzer.init_corpus = RPE.process_one_file(MIFuzzer.pcap)
        MIFuzzer.symbols = RPE.get_symbols(MIFuzzer.init_corpus)
        MIFuzzer.symbols_name = [s.name for s in MIFuzzer.symbols.values()]

    @staticmethod
    def get_corpus():
        return MIFuzzer.init_corpus

    @staticmethod
    def get_symbols(ret_list:bool=False):
        if ret_list: return list(MIFuzzer.symbols.values())
        return MIFuzzer.symbols

    @staticmethod
    def get_all_msg_by_symbols():
        assert MIFuzzer.symbols is not None
        for sym in MIFuzzer.symbols:
            MIFuzzer.sym_per_msg[MIFuzzer.symbols[sym]] = set(MIFuzzer.symbols[sym].getValues())
        return MIFuzzer.sym_per_msg

    @staticmethod
    def get_symbols_name():
        return MIFuzzer.symbols_name

