'''
'''

from rexfw.communicators import AbstractCommunicator


class MockCommunicator(AbstractCommunicator):

    def __init__(self):
        self.sent = []

    def send(self, obj, dest):
        self.sent.append([obj, dest])

    def recv(self, source):
        pass


class WorkHeatSendingMockCommunicator(AbstractCommunicator):

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
