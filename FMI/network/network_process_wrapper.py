import socket
import psutil
import time
from FMI.utils.decorators import FMILogger
from FMI.network.process_wrapper import ProcessWrapper

@FMILogger
class NetworkProcessWrapperMaker(object):

    def __init__(self, command_line, listen_ip, listen_port, restart_process=False, name=None):
        self.name = name
        self.command_line = command_line
        self.listen_ip = listen_ip
        self.listen_port = listen_port
        self.restart_process = restart_process
        self.__current_wrapper = None
        self._env = None

    def is_ready(self):
        if self.__current_wrapper is None:
            raise Exception("No current wrapper known, cannot stop it")
        return self.__current_wrapper.is_ready()

    def start(self):
        if self.__current_wrapper is not None:
            if not self.restart_process:
                return self.__current_wrapper

            raise Exception("Cannot start a new Network process wrapper, one already exists")
        self.__current_wrapper = NetworkProcessWrapper(
                                                    name=self.name,
                                                    command_line=self.command_line,
                                                    listen_ip=self.listen_ip,
                                                    listen_port=self.listen_port)
        self.__current_wrapper.env = self._env
        self.__current_wrapper.start()

    def stop(self, force=True):
        if self.__current_wrapper is None:
            #self._logger.info("No current wrapper known, cannot stop it")
            return
        if force or self.restart_process:
            self.__current_wrapper.stop()
            self.__current_wrapper = None

    def process_pid(self):
        if self.__current_wrapper:
            return self.__current_wrapper.process_pid

    def restart(self):
        self.stop(force=True)
        time.sleep(0.01)
        self.start()

    def update_env(self, identifier):
        self._env = identifier

    def __str__(self):
        return self.__current_wrapper.__str__()

@FMILogger
class NetworkProcessWrapper(ProcessWrapper):

    def __init__(self, command_line, listen_ip, listen_port, name=None):
        super(NetworkProcessWrapper, self).__init__(command_line=command_line, name=name)
        self.listen_ip = listen_ip
        self.listen_port = listen_port

    def __str__(self):
        if self.alive() and self.process_pid is not None:
            return "Process '{}' alive since {} (PID={}, CLI={}, listen={}:{}) ".format(self.name, self.started_at, self.process_pid, self.command_line, self.listen_ip, self.listen_port)

        else:
            return "Process '{}' (CLI={}, listen={}:{})".format(self.name, self.command_line, self.listen_ip, self.listen_port)


