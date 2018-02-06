'''
'''

from rexfw.communicators import AbstractCommunicator


class MockCommunicator(AbstractCommunicator):

    def __init__(self):
        self.last_sent = None
        self.last_dest = None
        self.last_received = None
        self.last_source = None

    def send(self, obj, dest):
        self.last_sent = obj
        self.last_dest = dest

    def recv(self, source):
        self.last_source = source
