import logging
import colorama
from functools import wraps
import os
from FMI.utils import constants

__all__ = [
    "TextFormatter",
    "ColorTextFormatter"
]
#LOG_EXTENSION = ".log"
class TextFormatter(logging.StreamHandler):

    def __init__(self, *args, **kwargs):
        super(TextFormatter, self).__init__(*args, **kwargs)

    def emit(self, record):
        try:
            message = self.format(record)
            self.stream.write(message)
            self.stream.write(getattr(self, 'terminator', '\n'))
            self.flush()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)

# use colored output and use different colors for different levels

class ColorTextFormatter(logging.StreamHandler):
    __logging_colors = {logging.INFO : colorama.Fore.GREEN, logging.WARNING : colorama.Fore.YELLOW,\
            logging.ERROR: colorama.Fore.RED, logging.DEBUG: colorama.Fore.CYAN,logging.CRITICAL: colorama.Back.RED + colorama.Fore.WHITE}

    def __init__(self, *args, **kwargs):
        super(ColorTextFormatter, self).__init__(*args, **kwargs)

    @property
    def is_tty(self):
        try:
            return getattr(self.stream, 'isatty', None)()
        except:
            return False

    def emit(self, record):
        try:
            message = self.format(record)
            if not self.is_tty:
                self.stream.write(message)
            else:
                self.stream.write(ColorTextFormatter.__logging_colors.get(record.levelno, colorama.Fore.BLACK) + message + colorama.Style.RESET_ALL)
            self.stream.write(getattr(self, 'terminator', '\n'))
            self.flush()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)




def FMILogger(klass):

    found = False
    for k, v in klass.__dict__.items():
        if isinstance(v, logging.Logger):
            found = True
            break

    if not found:
        klass._logger = logging.getLogger(klass.__name__)
        try:
            handler = ColorTextFormatter()
        except:
            handler = TextFormatter()
        #handler = ColorTextFormatter() if has_colour else TextFormatter()
        file_handler = logging.FileHandler(constants.LOGGER_GLOBAL_NAME + constants.LOG_EXTENSION)
        handler.setLevel(logging.ERROR)
        file_handler.setLevel(logging.DEBUG)
        fmt = '[%(levelname)s] %(asctime)s %(module)s:%(funcName)s: %(message)s'
        log_fmt = logging.Formatter(fmt)
        handler.setFormatter(log_fmt)
        file_handler.setFormatter(log_fmt)
        klass._logger.setLevel(logging.DEBUG)
        klass._logger.addHandler(handler)
        klass._logger.addHandler(file_handler)
        klass._logger.propagate = False

    def get_state(self, **kwargs):
        r = dict()
        for k, v in self.__dict__.items():
            if not isinstance(v, logging.Logger):
                r[k] = v

        return r

    def set_state(self, dict):
        self.__dict__ = dict
        self.__logger = logging.getLogger(klass.__name__)

    klass.__setstate__ = set_state
    klass.__getstate__ = get_state

    return klass

def typeCheck(*types):

    def _typeCheck_(func):
        def wrapped_f(*args, **kwargs):
            arguments = args[1:]
            if len(arguments) == len(types):
                final_types = []
                for type in types:
                    if type == "SELF":
                        final_types.append(args[0].__class__)
                    else:
                        final_type.append(type)

                for i, argument in enumerate(arguments):
                    if argument is not None and not isinstance(argument, final_types[i]):
                        raise TypeError("Invalid type for arguments, expecting: {0} and received {1}".format(', '.join([t.__name__ for t in final_types]), argument.__class__.__name__))
            return func(*args, **kwargs)
        return wraps(func)(wrapped_f)
    return _typeCheck_
