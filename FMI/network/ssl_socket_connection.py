import errno
import socket
import sys
from typing import Any, Optional

from future.utils import raise_

from FMI.utils import exception
from FMI.network.base_socket_connection import BaseSocketConnection
from FMI.utils import ip_constants

class SSLSocketConnection(TCPSocketConnection):

    def __init__(self, 
                host:str, 
                port:int, 
                send_timeout:float=5.0, 
                recv_timeout:float=5.0, 
                server:bool=False, 
                sslcontext:Optional[ssl.SSLContext]=None, 
                server_hostname:Optional[str]=None):
        super(SSLSocketConnection, self).__init__(host, port, send_timeout, recv_timeout, server)

        self.sslcontext = sslcontext
        self.server_hostname = server_hostname

        if self.server is True and self.sslcontext is None:
            raise ValueError("Parameter sslcontext is required when server=True.")
        if self.sslcontext is None and self.server_hostname is None:
            raise ValueError("SSL/TLS requires either sslcontext or server_hostname to be set.")

    def open(self) -> None:
        if self.server is False and self.sslcontext is None:
            self.sslcontext = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
            self.sslcontext.check_hostname = True
            self.sslcontext.verify_mode = ssl.CERT_REQUIRED

        super(SSLSocketConnection, self)._open_socket()

        # Create SSL socket
        try:
            self._sock = self.sslcontext.wrap_socket(
                self._sock, server_side=self.server, server_hostname=self.server_hostname
            )
        except ssl.SSLError as e:
            self.close()
            raise exception.BoofuzzTargetConnectionFailedError(str(e))
        except AttributeError:
            # No SSL context set
            pass

        super(SSLSocketConnection, self)._connect_socket()

    def recv(self, max_bytes: int = DEFAULT_MAX_RECV) -> Any:
        data = b""

        try:
            data = super(SSLSocketConnection, self).recv(max_bytes)
        except ssl.SSLError as e:
            raise_(exception.BoofuzzSSLError(str(e)))

        return data

    def send(self, data: Any) -> Any:
        num_sent = 0

        if len(data) > 0:
            try:
                num_sent = super(SSLSocketConnection, self).send(data)
            except ssl.SSLError as e:
                raise_(exception.BoofuzzSSLError(str(e)))

        return num_sent
