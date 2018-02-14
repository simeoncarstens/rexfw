'''
'''

from rexfw import Parcel

from rexfw.communicators import AbstractCommunicator

from collections import deque


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
