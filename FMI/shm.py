import abc
import atexit
import array
import os
import mmap

import sysv_ipc
import posix_ipc

from .utils.afl_constants import INSTR_AFL_MAP_SIZE
#from .utils import constants
from .utils import afl_constants
import random
import numpy as np
from .utils.helper import get_random_string
from multiprocessing import Lock

class AFLShm(abc.ABC):

    def __init__(self, identifier, size, mem):
        self._mem = mem
        self._identifier = identifier
        self._size = size
        self.history = [0] * INSTR_AFL_MAP_SIZE
        self._mut = Lock()

    @abc.abstractmethod
    def close(self):
        pass

    @property
    def name(self) -> str:
        return self._identifier

    def update_history(self, mem):
        snap = array.array('B', mem)
        for i, b in enumerate(snap):
            if b != 0 and not self.history[i]:
                self.history[i] = 1
        count = np.sum(self.history)
        return count

    def directed_branch_coverage(self):
        count = -1
        while True:
            snap = array.array('B', self.buf)
            for i, b in enumerate(snap):
                if b != 0 and not self.history[i]:
                    self.history[i] = 1
            tmp = np.sum(self.history)
            if count == tmp:
                break
            count = tmp
        return count

    def acquire(self):
        self._mut.acquire()

    def release(self):
        self._mut.release()

    @property
    def size(self) -> int:
        return self._size

    @property
    def buf(self) -> bytes:
        b = self._mem.read()
        return b


class AFLShmPOSIX(AFLShm):
    def __init__(self, identifier: int = None):
        if identifier is None and afl_constants.SHM_OVERWRITE == "":
            identifier = 'fml_afl_{}_{}'.format(get_random_string(4), get_random_string(12))
        elif afl_constants.SHM_OVERWRITE != "":
            identifier = afl_constants.SHM_OVERWRITE
        self.pobj = posix_ipc.SharedMemory(name=identifier, flags=os.O_CREAT,
                                           size=INSTR_AFL_MAP_SIZE)
        mem = mmap.mmap(self.pobj.fd, INSTR_AFL_MAP_SIZE)
        self.pobj.close_fd()
        super().__init__(identifier, INSTR_AFL_MAP_SIZE, mem)
        self._mem.write(b'\x00'*INSTR_AFL_MAP_SIZE)
        self._mem.seek(0)

    @property
    def buf(self) -> bytes:
        self._mem.seek(0)
        b = self._mem.read()
        self._mem.seek(0)
        return b

    def close(self):
        self._mem.close()

class AFLShmSYSV(AFLShm):
    def __init__(self, identifier: int = None):
        if identifier is None and afl_constants.SHM_OVERWRITE == "":
            identifier = random.randint(10000, 99999)
        elif afl_constants.SHM_OVERWRITE != "":
            identifier = int(afl_constants.SHM_OVERWRITE)
        super().__init__(identifier, INSTR_AFL_MAP_SIZE,
                         sysv_ipc.SharedMemory(key=identifier, flags=sysv_ipc.IPC_CREAT,
                                               size=INSTR_AFL_MAP_SIZE, init_character=b'\x00'))

    @property
    def name(self) -> str:
        return str(self._mem.id)

    def close(self):
        sysv_ipc.remove_shared_memory(self._mem.id)

__shm = None
__pkg_mut = Lock()

def get(identifier: str = None) -> AFLShm:
    """
    Allocate "singleton" linux SHM region which will be passed to instrumented binary.
    Identifier is randomly drawn from /dev/urandom within (MIN_UINT32_T, MAX_UINT32_T) if is None.

    :param identifier: AFLShm.name
    :return: AFLShm
    """
    __pkg_mut.acquire()
    global __shm
    if __shm is None:
        if afl_constants.SHM_POSIX:
            __shm = AFLShmPOSIX(identifier=identifier)
        else:
            __shm = AFLShmSYSV(identifier=identifier)
    __pkg_mut.release()
    return __shm


def recreate(identifier: int = None) -> AFLShm:
    """
    Recreate shared memory

    :param identifier: New Identifier, if none, take same identifier as last time
    :return: AFLShm
    """
    global __shm
    tmp = None
    if __shm is not None:
        tmp = __shm.name
        delete()
    return get(identifier=identifier if identifier is not None else tmp)


@atexit.register  # clear shm at exit so it won't leak
def delete():
    """
    Delete Shared Memory
    """
    global __shm
    if __shm is not None:
        __shm.close()
    __shm = None
