from FMI.utils.decorators import FMILogger

from netzob.Model.Vocabulary.Symbol import Symbol
from netzob.Model.Vocabulary.EmptySymbol import EmptySymbol
from netzob.Model.Vocabulary.Domain.Variables.Memory import Memory
from netzob.Model.Vocabulary.Domain.Specializer.MessageSpecializer import MessageSpecializer
from netzob.Model.Vocabulary.Domain.Parser.MessageParser import MessageParser
from netzob.Model.Vocabulary.Domain.Parser.FlowParser import FlowParser
from netzob.Model.Vocabulary.Types.TypeConverter import TypeConverter
from netzob.Model.Vocabulary.Types.BitArray import BitArray
from netzob.Model.Vocabulary.Types.Raw import Raw
from netzob.Model.Vocabulary.Messages.RawMessage import RawMessage
from netzob.Model.Vocabulary.UnknownSymbol import UnknownSymbol


@FMILogger
class AbstractionLayer(object):
    """ This class should convert symbols to real message and """
    def __init__(self, symbols):
        self.symbols = symbols
        self.memory = Memory()
        self.specializer = MessageSpecializer(memory=self.memory)
        self.parser = MessageParser(memory=self.memory)
        self.flow_parser = FlowParser(memory=self.memory)


    def convert_symbol_to_msg(self,symbol, presets=None):

        self.specializer.presets = presets
        dataBin = self.specializer.specializeSymbol(symbol).generatedContent
        self.specializer.presets = None
        self.memory = self.specializer.memory
        self.parser.memory = self.memory

        return TypeConverter.convert(dataBin, BitArray, Raw)



    def convert_msg_to_symbol(self,data):

        if len(data) <= 0:
            self._logger.debug("Data length should be greater than 0")
            return EmptySymbol()
        symbol = None
        for potential in self.symbols:
            try:
                self.parser.parseMessage(RawMessage(data), potential)
                symbol = potential
                self.memory = self.parser.memory
                self.specializer.memory = self.memory
                break
            except:
                symbol = None
        if symbol is None:
            msg = RawMessage(data)
            symbol = UnknownSymbol(message=msg)
            self.symbols.append(symbol)

        return symbol

    def convert_msg_to_unknownsymbol(self,data):
        """ TODO: Double check if data is already in self.symbols
            Assumption: data not in self.symbols
        """
        msg = RawMessage(data)
        symbol = UnknownSymbol(message=msg)
        for symb in self.symbols:
            if isinstance(symb, UnknownSymbol) and symb.message.data == data:
                return None
        self.symbols.append(symbol)
        return symbol




