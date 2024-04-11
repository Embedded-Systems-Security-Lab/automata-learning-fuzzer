""" From Boofuzz"""
import functools
import ipaddress
import logging
import socket
import struct
import sys
import threading
import time
import unittest
import zlib

from FMI.network.tcp_socket_connection import TCPSocketConnection
from FMI.network.udp_socket_connection import UDPSocketConnection
from FMI.utils import ip_constants


THREAD_WAIT_TIMEOUT = 10  # Time to wait for a thread before considering it failed.



class MiniTestServer:
    """
    Small server class for testing SocketConnection.
    """

    def __init__(self, stay_silent=False, proto="tcp", host="0.0.0.0"):
        self.server_socket = None
        self.received = None
        self.data_to_send = b"\xFE\xEB\xDA\xED"
        self.active_port = None
        self.stay_silent = stay_silent
        self.proto = proto
        self.host = host
        self.timeout = 5  # Timeout while waiting for the unit test packets.

    def bind(self):
        """
        Bind server, and call listen if using TCP, meaning that the client test code can successfully connect.
        """
        if self.proto == "tcp":
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        elif self.proto == "udp":
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        elif self.proto == "raw":
            self.server_socket = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.ntohs(ETH_P_ALL))
        else:
            raise Exception("Invalid protocol type: '{0}'".format(self.proto))

        self.server_socket.bind((self.host, 0))  # let OS choose a free port

        if self.proto == "tcp":
            self.server_socket.listen(1)

        self.active_port = self.server_socket.getsockname()[1]

    def serve_once(self):
        """
        Serve one connection and send a reply, unless stay_silent is set.
        :return:
        """
        self.server_socket.settimeout(self.timeout)

        if self.proto == "tcp":
            (client_socket, address) = self.server_socket.accept()
            client_socket.settimeout(self.timeout)

            self.received = client_socket.recv(10000)

            if not self.stay_silent:
                client_socket.send(self.data_to_send)

            client_socket.close()
        elif self.proto == "udp":
            data, addr = self.server_socket.recvfrom(1024)
            self.received = data
            if not self.stay_silent:
                self.server_socket.sendto(self.data_to_send, addr)
        elif self.proto == "raw":
            data, addr = self.server_socket.recvfrom(10000)
            self.received = data
            if not self.stay_silent:
                self.server_socket.sendto(self.data_to_send, addr)
        else:
            raise Exception("Invalid protocol type: '{0}'".format(self.proto))

        self.server_socket.close()
        self.server_socket = None
        self.active_port = None

    def receive_until(self, expected):
        """Receive repeatedly until expected is received.
        This is handy for a noisy socket (e.g., layer 2 or layer 3 sockets that
        receive data from multiple applications).
        Will send a reply to first connection, unless stay_silent is set.
        Puts received data in self.received if and only if expected is
        received.
        @param expected: Expected value to look for.
        """
        self.server_socket.settimeout(self.timeout)

        if self.proto == "raw":
            # Keep receiving
            elapsed_time = 0
            start_time = time.time()
            while elapsed_time < self.timeout:
                self.server_socket.settimeout(self.timeout - elapsed_time)
                try:
                    data, addr = self.server_socket.recvfrom(10000)
                    if data == expected:
                        self.received = data
                        if not self.stay_silent:
                            self.server_socket.sendto(self.data_to_send, addr)
                        break
                except socket.timeout:
                    break
                elapsed_time = time.time() - start_time
        else:
            raise Exception("Invalid protocol type: '{0}'".format(self.proto))

        self.server_socket.close()
        self.server_socket = None
        self.active_port = None

class TestSocketConnection(unittest.TestCase):

    def test_tcp_client(self):

        data_to_send = b"uuddlrlrba"

        # Given
        server = MiniTestServer()
        server.bind()

        t = threading.Thread(target=server.serve_once)
        t.daemon = True
        t.start()

        uut = TCPSocketConnection(host=socket.gethostname(), port=server.active_port)
        #uut.logger = logging.getLogger("SulleyUTLogger")

        # When
        uut.open()
        send_result = uut.send(data=data_to_send)
        received = uut.recv(10000)
        uut.close()

        # Wait for the other thread to terminate
        t.join(THREAD_WAIT_TIMEOUT)
        self.assertFalse(t.is_alive())

        # Then
        self.assertEqual(send_result, len(data_to_send))
        self.assertEqual(data_to_send, server.received)
        self.assertEqual(received, server.data_to_send)

    def test_tcp_client_timeout(self):

        data_to_send = b"uuddlrlrba"

        # Given
        server = MiniTestServer(stay_silent=True)
        server.bind()

        t = threading.Thread(target=server.serve_once)
        t.daemon = True
        t.start()

        uut = TCPSocketConnection(host=socket.gethostname(), port=server.active_port)
        uut.logger = logging.getLogger("SulleyUTLogger")

        # When
        uut.open()
        send_result = uut.send(data=data_to_send)
        received = uut.recv(10000)
        uut.close()

        # Wait for the other thread to terminate
        t.join(THREAD_WAIT_TIMEOUT)
        self.assertFalse(t.is_alive())

        # Then
        self.assertEqual(send_result, len(data_to_send))
        self.assertEqual(data_to_send, server.received)
        self.assertEqual(received, b"")
