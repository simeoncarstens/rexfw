'''
'''

import unittest
from collections import deque

from rexfw import Parcel
from rexfw.communicators import AbstractCommunicator
from rexfw.communicators.mpi import MPICommunicator


class MockCommunicator(AbstractCommunicator):

    def __init__(self):
        self.sent = deque()
        self.received = deque()

    def send(self, obj, dest):
        self.sent.append([obj, dest])

    def recv(self, source):

        obj = Parcel(source, 'remaster0', None)
        self.received.append([obj, source])

        return obj


class WorkHeatReceivingMockCommunicator(MockCommunicator):

    def send(self, obj, dest):
        pass

    def calculate_work_from_source(self, source):
        return (int(source[-1]) + 1) ** 2
    
    def calculate_heat_from_source(self, source):
        return (int(source[-1]) + 2) ** 2

    def recv(self, source):

        from rexfw import Parcel
        
        return Parcel(source, 'remaster0',
                      (self.calculate_work_from_source(source),
                       self.calculate_heat_from_source(source)))


class DoNothingRequestReceivingMockCommunicator(MockCommunicator):

    def __init__(self):

        super(DoNothingRequestReceivingMockCommunicator, self).__init__()

        self.received = deque()
        
    def recv(self, source):

        from rexfw import Parcel
        from rexfw.replicas.requests import DoNothingRequest

        parcel = Parcel(source, 'remaster0', DoNothingRequest(source))
        self.received.append(parcel)
        
        return parcel


class testMPICommnicator(unittest.TestCase):

    def setUp(self):

        self._comm = MPICommunicator()

    def testDestToRank(self):

        pairs = (('replica6', 6), ('replica13', 13), ('replica133', 133),
                 ('master0', 0), ('master10', 10))

        for dest, rank in pairs:
            self.assertEqual(self._comm._dest_to_rank(dest), rank)


if __name__ == '__main__':

    unittest.main()
