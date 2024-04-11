import pickle
import struct

class Replay(object):

    @staticmethod
    def read_data(file_path):
        with open(file_path, 'rb') as f:
            data = pickle.load(f)
        return data

    @staticmethod
    def replay_data_afl(file_path):
        packet_count = 0
        seq = list()
        size_of_unsigned_int = struct.calcsize('I')
        with open(file_path, 'rb') as f:
            while True:
                data = f.read(size_of_unsigned_int)
                if not data:
                    break
                size = struct.unpack('I', data)[0]
                if size:
                    packet_count += 1
                    buf = f.read(size)
                    seq.append(buf)
        return seq