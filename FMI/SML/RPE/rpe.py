from netzob.all import *
import os
from binascii import *
from FMI.utils.decorators import FMILogger

@FMILogger
class RPE(object):

    __pcap = '.pcap'

    @staticmethod
    def process_one_file(file_path):
        if not os.path.exists(file_path):
            raise Exception("File path not found")
        if not file_path.endswith(RPE.__pcap):
            raise Exception("This method can only process pcap files")
        try:
            message = PCAPImporter.readFile(file_path).values()
        except:
            self._logger.debug("Cannot process the pcap file: {}".format(file_path))
            return
        return message

    @staticmethod
    def process_multiple_pcap_file(folder):
        if not os.path.isdir(folder):
            raise Exception("Please provide a folder path")
        messages = None
        for file_name in os.listdir(folder):
            file_path = os.path.join(folder, file_name)
            if file_path.endswith(RPE.__pcap):
                try:
                    if messages is None:
                        messages = PCAPImporter.readFile(file_path).values()
                    else:
                        messages += PCAPImporter.readFile(file_path).values()
                except:
                    self._logger.debug("Cannot process the pcap file: {}".format(file_path))

        return messages

    @staticmethod
    def get_symbols(messages):
        symbol = Symbol(messages=messages)
        Format.splitStatic(symbol)
        symbols = Format.clusterByKeyField(symbol, symbol.fields[-1])
        for symbol in symbols.values():
            rels = RelationFinder.findOnSymbol(symbol)
            for rel in rels:
                rel = rels[0]
                rel["x_fields"][0].domain = Size(rel["y_fields"], factor=1/8.0)
        return symbols

