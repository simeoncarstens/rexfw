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
            
    def send(self, obj, dest):
        if not self.whatsnext == "send":
            raise ValueError("Communicator expecting to {0} instead of {1}".format(self.whatsnext,
                                                                                   "send"))
        self.comm.send(obj, dest=self._dest_to_rank(dest))

    def recv(self, source):
        if not self.whatsnext == "send":
            raise ValueError("Communicator expecting to {0} instead of {1}".format(self.whatsnext,
                                                                                   "receive"))
        if source == 'all':
            source = MPI.ANY_SOURCE
        return self.comm.recv(source=source)
