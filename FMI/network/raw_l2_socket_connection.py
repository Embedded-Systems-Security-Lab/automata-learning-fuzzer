import errno
import socket
import sys
from typing import Tuple, Union, Any

from future.utils import raise_

from FMI.utils import exception
from FMI.network.base_socket_connection import BaseSocketConnection
from FMI.utils import ip_constants
"""Got from Boofuzz"""
class RawL2SocketConnection(BaseSocketConnection):

    def __init__(self,
        interface:str,
        send_timeout:float=5.0,
        recv_timeout:float=5.0,
        ethernet_proto:int=0,
        mtu:int=1518,
        has_framecheck:bool=True):
        super(RawL2SocketConnection, self).__init__(send_timeout, recv_timeout)

        self._interface = interface
        self._ethernet_proto = ethernet_proto
        self._mtu = mtu
        self._has_framecheck = has_framecheck
        self._max_send_size = mtu
        if self._has_framecheck:
            self._max_send_size -= 4

    def open(self) -> None:
        self._sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(self._ethernet_proto))
        self._sock.bind((self._interface, self._ethernet_proto))

        super(RawL2SocketConnection, self).open()

    def recv(self, max_bytes: int = ip_constants.DEFAULT_MAX_RECV) -> Any:
        if self._ethernet_proto is None:
            raise Exception(
                "Receiving on Raw Layer 2 sockets is only supported if the socket "
                "is bound to an interface and protocol."
            )

        data = b""

        try:
            data = self._sock.recv(self.mtu)

            if 0 < len(data) < max_bytes:
                data = data[:max_bytes]
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

        return data

    def send(self, data: Any) -> Any:
        num_sent = 0

        data = data[: self._max_send_size]

        try:
            num_sent = self._sock.send(data)

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

    @property
    def info(self):
        return "{}, type 0x{:04x}".format(self._interface, self._ethernet_proto)
