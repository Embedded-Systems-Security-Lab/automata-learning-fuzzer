import time
import os
from typing import List, TYPE_CHECKING, Any, Tuple, Optional

from FMI.utils.ip_constants import DEFAULT_MAX_RECV
from FMI.utils import exception
from FMI import shm
from FMI.utils.server_status import SUT_STATUS
from FMI.utils.helper import critical_signals_nix

if TYPE_CHECKING:
    from FMI.session import Session




class TestCase(object):
    """TODO: Remove the self.buf, waste of memory"""
    def __init__(self, id: str, session: 'Session', sequence: list):

        self.id = id
        self.session = session
        self.sequence = sequence
        self.needed_restart = False
        self.done = False
        self.last_cov = None

    @property
    def coverage_snapshot(self):
        mem = shm.get()
        mem.acquire()
        self.last_cov = mem.directed_branch_coverage()
        buf = mem.buf
        mem.release()
        return self.last_cov, buf

    def determine_crtitical_nature(self, err_code):
        if err_code and os.WIFSIGNALED(err_code):
            return True
        return False

    def run(self, new_payload, is_rec=True, s_time=0.000001) -> Tuple[Optional[Exception], bool, Optional[SUT_STATUS]]:

        status = SUT_STATUS.NO_CRASH
        try:
            self.session.restarter.restart(planned=True)
            self.open_fuzzing_target()
            # process pre-phase of population for state transitions
            for payload in self.sequence:
                self.transmit(payload, receive=is_rec)
            # fuzz individual
            if not self.session.restarter.healthy():
                return None, False, SUT_STATUS.CRASH_BEFORE_SEND

            self.transmit(new_payload, receive=is_rec)
            time.sleep(s_time)
            if not self.session.restarter.healthy():
                self.session.restarter.p.poll()
                code = self.session.restarter.p.returncode
                is_critical = self.determine_crtitical_nature(code)
                if is_critical:
                    status = SUT_STATUS.CRASH_AFTER_SEND
                else:
                    status = SUT_STATUS.DISCONNECTED
            try:
                self.session.target.close()
            except Exception:
                pass
            self.done = True
            return None, True, status
        except exception.FMIPaused as e:
            return e, False, status  # Returns False when the fuzzer got paused, as it did not run the TestCase
        except exception.FMITestCaseAborted as e:  # There was a transmission Error, we end the test case
            return e, False, status
        except Exception as e:
            return e, False, status

    def run_seq(self):
        try:
            self.session.restarter.restart(planned=True)
            self.open_fuzzing_target()
            for payload in self.sequence:
                self.transmit(payload, receive=False)
            if not self.session.restarter.healthy():
                return False
        except:
            return False
        return True

    def open_fuzzing_target(self):

        target = self.session.target
        try:
            target.open()
        except (exception.FMITargetConnectionFailedError, Exception):
            for i in range(0, 3):
                try:
                    time.sleep(0.000001)
                    target.open()  # Second try, just in case we have a network error not caused by the fuzzer
                except Exception:
                    pass
            try:
                target.open()
            except Exception as e:
                raise exception.FMITargetConnectionFailedError()


    def transmit(self, data: bytes, receive=False, relax=False):
        # 1. SEND DATA
        try:
            self.session.target.send(data)
        except Exception as e:
            if not relax:
                raise e
        # 2. RECEIVE DATA
        if receive:
            try:
                last_recv = self.session.target.recv(DEFAULT_MAX_RECV)
                # print("Receving {}".format(last_recv))
            except Exception as e:
                raise e

    # --------------------------------------------------------------- #

    def __repr__(self):
        return f'{vars(self)}'
