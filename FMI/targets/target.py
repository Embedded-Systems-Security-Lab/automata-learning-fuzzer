from FMI.utils.ip_constants import DEFAULT_MAX_RECV
from copy import deepcopy


class Target(object):

    def __init__(self, connection):
        self.target_connection = connection

    def close(self):
        self.target_connection.close()

    def open(self):
        self.target_connection.open()

    def recv(self, max_bytes: int = DEFAULT_MAX_RECV):

        data = self.target_connection.recv(max_bytes=max_bytes)

        return data

    def recv_all(self, max_bytes: int = DEFAULT_MAX_RECV):

        data = self.target_connection.recv_all(max_bytes=max_bytes)

        return data

    def send(self, data):
        num_sent = self.target_connection.send(data=data)
        return num_sent
