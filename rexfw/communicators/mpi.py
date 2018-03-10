'''
'''

from rexfw.communicators import AbstractCommunicator
from mpi4py import MPI


class MPICommunicator(AbstractCommunicator):

    comm = MPI.COMM_WORLD

    def _dest_to_rank(self, dest):

        if type(dest) == str:
            if 'replica' in dest:
                return int(dest[len('replica'):])
            if 'master' in dest:
                return int(dest[len('master'):])
            if dest == 'all':
                return MPI.ANY_SOURCE

    def send(self, obj, dest):

        rank = self._dest_to_rank(dest)
        self.comm.send(obj, dest=rank)

    def recv(self, source):

        rank = self._dest_to_rank(source)

        return self.comm.recv(source=rank)

    def sendrecv(self, obj, dest):

        rank = self._dest_to_rank(dest)

        return self.comm.sendrecv(obj, dest=rank)
        
