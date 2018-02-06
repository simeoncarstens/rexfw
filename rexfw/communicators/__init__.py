'''
Communicator classes which handle communication between master and slaves
'''

from abc import abstractmethod

class AbstractCommunicator(object):

    @abstractmethod
    def send(self, obj, dest):
        pass

    @abstractmethod
    def recv(self, source):
        pass
    
    
