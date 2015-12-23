'''
Slave classes responsible for distributing requests to replicas, proposers, ...
'''

from rexfw import Parcel


class Slave(object):

    def __init__(self, replicas, comm):

        self.replicas = replicas
        self._comm = comm

    def _listen(self):

        while True:
            parcel = self._receive_parcel()
            if parcel.receiver in self.replicas.iterkeys():
                result = self.replicas[parcel.receiver].process_request(parcel.data)                
                if result == -1:
                    break
            else:
                raise ValueError("Replica '{}' not found.".format(parcel.receiver))

    def listen(self):

        from threading import Thread

        self._thread = Thread(target=self._listen)
        self._thread.start()

    def _receive_parcel(self):

        return self._comm.recv(source=-1)
