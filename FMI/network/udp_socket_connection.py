
import ctypes
import errno
import platform
import socket
import sys
from typing import Tuple, Union, Any

from future.utils import raise_

from FMI.utils import exception
from FMI.network.base_socket_connection import BaseSocketConnection
from FMI.utils.ip_constants import *


class UDPSocketConnection(BaseSocketConnection):

    _max_payload = None

    def __init__(self,
                host:str,
                port:str,
                send_timeout:float=5.0,
                recv_timeout:float=5.0,
                server:bool=False,
                bind:Union[Tuple[str, str], None]=None,
                broadcast:bool=False):
        super(UDPSocketConnection, self).__init__(send_timeout, recv_timeout)
        self._host = host
        self._port = port
        self._server = server
        self._bind = bind
        self._broadcast = broadcast

        self._serverSocket = None
        self._udp_client_port = None

        self.max_payload()
        if self._bind and self._server:
            raise Exception("You cannot set both bind and server at the same time.")

    def open(self) -> None:

        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if self._bind:
            self._sock.bind(self._bind)
        super(UDPSocketConnection, self).open()

        if self._server:
            self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._sock.bind((self._host, self._port))

    def recv(self, max_bytes: int = DEFAULT_MAX_RECV) -> Any:

        data = b""
        try:
            if self._bind or self._server:
                data, self._udp_client_port = self._sock.recvfrom(max_bytes)
            else:
                raise exception.FMIRuntimeError(
                    "UDPSocketConnection.recv() requires a bind address/port." " Current value: {}".format(self._bind)
                )

        except socket.timeout:
            data = b""
        except socket.error as e:
            if e.errno == errno.ECONNABORTED:
                raise_(
                    exception.FMITargetConnectionAborted(socket_errno=e.errno, socket_errmsg=e.strerror),
                    None,
                    sys.exc_info()[2],
                )
            elif e.errno in [errno.ECONNRESET, errno.ENETRESET, errno.ETIMEDOUT]:
                raise_(exception.FMITargetConnectionReset(), None, sys.exc_info()[2])
            elif e.errno == errno.EWOULDBLOCK:
                data = b""
            else:
                raise

    def send(self, data: Any) -> Any:

        num_sent = 0
        data = data[:UDPSocketConnection._max_payload]
        try:
            if self._server:
                if self._udp_client_port is None:
                    raise exception.FMIError("recv() must be called before send with udp fuzzing servers.")

                num_sent = self._sock.sendto(data, self._udp_client_port)
            else:
                num_sent = self._sock.sendto(data, (self._host, self._port))
        except socket.error as e:
            if e.errno == errno.ECONNABORTED:
                raise_(
                    exception.FMITargetConnectionAborted(socket_errno=e.errno, socket_errmsg=e.strerror),
                    None,
                    sys.exc_info()[2],
                )
            elif e.errno in [errno.ECONNRESET, errno.ENETRESET, errno.ETIMEDOUT, errno.EPIPE]:
                raise_(exception.FMITargetConnectionReset(), None, sys.exc_info()[2])
            else:
                raise

        return num_sent

    @classmethod
    def max_payload(cls):

        if cls._max_payload is not None:
            return cls._max_payload

        windows = platform.uname()[0] == "Windows"
        mac = platform.uname()[0] == "Darwin"
        linux = platform.uname()[0] == "Linux"
        openbsd = platform.uname()[0] == "OpenBSD"
        lib = None

        if windows:
            sol_socket = ctypes.c_int(0xFFFF)
            sol_max_msg_size = 0x2003
            lib = ctypes.WinDLL("Ws2_32.dll")
            opt = ctypes.c_int(sol_max_msg_size)
        elif linux or mac or openbsd:
            if mac:
                lib = ctypes.cdll.LoadLibrary("libc.dylib")
            elif linux:
                lib = ctypes.cdll.LoadLibrary("libc.so.6")
            elif openbsd:
                lib = ctypes.cdll.LoadLibrary("libc.so")
            sol_socket = ctypes.c_int(socket.SOL_SOCKET)
            opt = ctypes.c_int(socket.SO_SNDBUF)

        else:
            raise Exception("Unknown platform!")

        ulong_size = ctypes.sizeof(ctypes.c_ulong)
        buf = ctypes.create_string_buffer(ulong_size)
        bufsize = ctypes.c_int(ulong_size)

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        lib.getsockopt(sock.fileno(), sol_socket, opt, buf, ctypes.pointer(bufsize))

        # Sanity filter against UDP_MAX_PAYLOAD_IPV4_THEORETICAL
        cls._max_payload = min(ctypes.c_ulong.from_buffer(buf).value, UDP_MAX_PAYLOAD_IPV4_THEORETICAL)

        return cls._max_payload



    @property
    def info(self) -> str:
        return "{}:{}".format(self._host, self._port)





