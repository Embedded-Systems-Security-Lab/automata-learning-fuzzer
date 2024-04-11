from threading import Thread, Event
import shlex
from subprocess import Popen, PIPE
import subprocess
from queue import Queue, Empty
import os
import signal
from datetime import datetime
import psutil

from FMI.utils.decorators import FMILogger

# @FMILogger
# class NonBlockingStreamReader(object):

#     def __init__(self, stream):

#         self._s = stream
#         self._q = Queue()
#         self.__stopEvent = Event()

#         def _populateQueue(stream, queue):
#             for item in stream:
#                 queue.put(item)

#         self._t = Thread(target = _populateQueue, args = (self._s, self._q))
#         self._t.daemon = True
#         self._t.start()

#     def readline(self, timeout = None):
#         try:
#             return self._q.get(
#                 block = timeout is not None,
#                 timeout = timeout)
#         except Empty:
#             return None

#     def print_content_queue(self):
#         for val in self._q.queue():
#             self._logger.debug(val)

#     def stop(self):
#         self.__stopEvent.set()

# class UnexpectedEndOfStream(Exception): pass

@FMILogger
class ProcessWrapper(Thread):

    def __init__(self, command_line, name=None):

        Thread.__init__(self)
        self.__flag_stop = False
        self.__process_pid = None
        self.__process = None
        self.__process_psutils = None

        self.name = name
        self.command_line = command_line
        self.started_at = None
        self._env = {}

        self.outputs = []


    def __str__(self):
        if self.alive() and self.__process_pid is not None:
            return "{} alive since {} (PID={}, CLI={}) ".format(self.name, self.started_at, self.__process_pid, self.command_line)
        else:
            return "{} (CLI={})".format(self.name, self.command_line)

    def run(self):

        #self._logger.info("Starting process '{}' ({})".format(self.name, self.command_line))

        args = shlex.split(self.command_line)
        self.__process = Popen(args, env=self._env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=False,start_new_session=True, close_fds=True)
        self.__process_pid = self.__process.pid
        self.__process_psutils = psutil.Process(self.__process_pid)
        self.started_at = datetime.utcnow()

        #self._logger.debug("Process {} started (PID={})".format(self.name, self.__process_pid))


        # streamReader_stdout = NonBlockingStreamReader(self.__process.stdout)
        # streamReader_stderr = NonBlockingStreamReader(self.__process.stderr)
        # while not self.__flag_stop:
        #     output = streamReader_stdout.readline(0.01)
        #     if output:
        #         self.outputs.append(output)
        #         self._logger.info(output.strip())
        #     error = streamReader_stderr.readline(0.01)
        #     if error:
        #         self._logger.error(error.strip())
        #         self.outputs.append(error)
        # streamReader_stdout.stop()
        # streamReader_stderr.stop()

    @property
    def env(self):
        return self._env

    @env.setter
    def env(self, identifier):
        self._env = identifier



    def stop(self):
        self.__flag_stop = True

        self._logger.info("Stopping process '{}' (PID={})".format(self.name, self.__process_pid))
        status = self.alive()
        if status:
            self.kill_all()

    def alive(self):
        if self.__process is None: return False
        if psutil.pid_exists(self.__process.pid):
            status = None
            try:
                status = self.__process_psutils.status()
            except psutil.NoSuchProcess as exc:
                return False
            if status and status == psutil.STATUS_ZOMBIE:
                self.kill_all()
                return False
            return True

        return False

    def kill_all(self):
        if self.__process is None: return
        try:
            parent = psutil.Process(self.__process.pid)
            children = parent.children(recursive=True)
        except psutil.NoSuchProcess as exc:
            return
        for p in children:
            self.kill_process(p)
        self.kill_process(parent)

    def kill_process(self, proc):
        try:
            proc.send_signal(signal.SIGKILL)
        except:
            try:
                os.system("sudo kill {}".format(proc))
            except:
                pass

    @property
    def process_pid(self):
        return self.__process_pid

    @property
    def process_psutils(self):
        return self.__process_psutils

    def is_ready(self):
        try:
            if self.process_psutils and self.process_psutils.status() in [psutil.STATUS_RUNNING, psutil.STATUS_SLEEPING]:
                return True
        except psutil.NoSuchProcess as exc:
            pass
        #print("It's not ready")
        return False
