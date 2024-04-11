import errno
import socket
import sys
from typing import Any, ByteString

from future.utils import raise_

from FMI.utils import exception
from FMI.network.base_socket_connection import BaseSocketConnection
from FMI.utils import ip_constants

ETH_P_ALL = 0x0003
ETH_P_IP = 0x0800

class RawL3SocketConnection(BaseSocketConnection):

    def __init__(
        self,
        interface:str,
        send_timeout:float=5.0,
        recv_timeout:float=5.0,
        ethernet_proto:float=ETH_P_IP,
        l2_dst:ByteString=b"\xff" * 6,
        packet_size:int=1500,
    ):
        super(RawL3SocketConnection, self).__init__(send_timeout, recv_timeout)

        self._interface = interface
        self._ethernet_proto = ethernet_proto
        self._l2_dst = l2_dst
        self._packet_size = packet_size

    def open(self) -> None:
        self._sock = socket.socket(socket.AF_PACKET, socket.SOCK_DGRAM, socket.htons(self._ethernet_proto))
        self._sock.bind((self._interface, self._ethernet_proto))

        super(RawL3SocketConnection, self).open()

    def recv(self, max_bytes: int = ip_constants.DEFAULT_MAX_RECV) -> Any:
        data = b""

        try:
            data = self._sock.recv(self._packet_size)

            if 0 < max_bytes < self._packet_size:
                data = data[: self._packet_size]

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

        data = data[: self.packet_size]

        try:
            num_sent = self._sock.sendto(data, (self._interface, self._ethernet_proto, 0, 0, self._l2_dst))

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
