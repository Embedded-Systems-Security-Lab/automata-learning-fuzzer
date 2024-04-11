import subprocess
import time
import shlex
import os
import psutil
import re

from .irestarter import IRestarter
from FMI.utils.afl_constants import INSTR_AFL_ENV
from FMI.utils import afl_constants
from .. import shm


class AFLForkRestarter(IRestarter):

    def __init__(self, cmd, *args, **kwargs):
        self.cmd = cmd
        self._argv = shlex.split(self.cmd)
        self._path = self._argv[0]
        self.process = None
        self.restarts = 0
        self.crashes = 0
        self.cid = None

    @staticmethod
    def name() -> str:
        return afl_constants.AFL_WITHOUT_FORKSERVER

    @staticmethod
    def help() -> str:
        return "'<executable> [<argument> ...]' (Pass command and arguments within quotes, as only one argument)"

    def restart(self, *args, planned=False) -> bool:
        """
        Restarts the target

        :param args: ignored
        :param kwargs: ignored
        :return: bool
        """
        try:
            mem = shm.get()
            mem.acquire()
            identifier = mem.name  # get instrumentation shared memory id
            mem.release()
            environ = _update_env(identifier)  # add pseudorandom shm identifier to environment variable of child process
            self.kill()
            self.p = self._fork(environ)  # actually fork
            self.process = psutil.Process(self.p.pid)
            if not self._wait_for_status(psutil.STATUS_SLEEPING, timeout=1.0):
                return False
        except Exception as e:
            return False
        if not planned:
            self.restarts += 1
        return self.healthy()

    def _wait_for_status(self, status: str, timeout: float = 1.0, sleep_time: float = 0.0001, negate: bool = False) -> bool:
        if self.process is None:
            return False
        cumulative_t = 0.0
        try:
            if not negate:
                while self.process.status() is not status:
                    # we are literally waiting for the process to wait on its socket
                    if cumulative_t >= timeout:
                        return False
                    time.sleep(sleep_time)
                    cumulative_t += sleep_time
            else:
                while self.process.status() is status:
                    # we are literally waiting for the process to wait on its socket
                    if cumulative_t >= timeout:
                        return False
                    time.sleep(sleep_time)
                    cumulative_t += sleep_time
        except Exception:
            return False
        return True

    def kill(self):
        if not self.process: return
        try:
            self.process.kill()
        except:
            try:
                subprocess.check_output("sudo kill {}".format(self.p.pid))
            except:
                pass

    def healthy(self) -> bool:
        try:
            return self.process is not None and self.process.status() not in [psutil.STATUS_DEAD, psutil.STATUS_ZOMBIE]
        except Exception:
            return False

    def _fork(self, environ: {}) -> int:
        p = subprocess.Popen(args=self._argv,
                               shell=False,
                               env=environ,
                               stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL,
                               start_new_session=True,
                               close_fds=True)
        return p

def _update_env(identifier: str) -> {}:
    environ = os.environ.copy()
    environ[INSTR_AFL_ENV] = str(identifier)
    return environ
