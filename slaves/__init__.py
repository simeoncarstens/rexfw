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
                    # import numpy
                    # numpy.save('/scratch/scarste/rens/re_long_udcounts_marginal_10replicas_nperturb2_nrelax2_nequsteps100/rep0/statistics/up_down_counts_{}.npy'.format(self.replicas[self.replicas.keys()[0]].name), self.replicas[self.replicas.keys()[0]].up_down_counts)
                    break
            else:
                raise ValueError("Replica '{}' not found.".format(parcel.receiver))

    def listen(self):

        from threading import Thread

        self._thread = Thread(target=self._listen)
        self._thread.start()

    def _receive_parcel(self):

        return self._comm.recv(source='all')


class UDCountsSlave(object):

    def __init__(self, replicas, comm, sim_path):

        self.replicas = replicas
        self._comm = comm
        self._sim_path = sim_path

    def _listen(self):

        while True:
            parcel = self._receive_parcel()
            if parcel.receiver in self.replicas.iterkeys():
                result = self.replicas[parcel.receiver].process_request(parcel.data)                
                if result == -1:
                    import numpy
                    replica_name = self.replicas[self.replicas.keys()[0]].name
                    numpy.save(self._sim_path + 'statistics/up_down_counts_{}.npy'.format(replica_name),
                               self.replicas[replica_name].up_down_counts)
                    break
            else:
                raise ValueError("Replica '{}' not found.".format(parcel.receiver))

    def listen(self):

        from threading import Thread

        self._thread = Thread(target=self._listen)
        self._thread.start()

    def _receive_parcel(self):

        return self._comm.recv(source='all')
