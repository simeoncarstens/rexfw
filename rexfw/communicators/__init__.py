'''
Communicator classes which handle communication between master and slaves
'''

from abc import abstractmethod

class AbstractCommunicator(object):

    @abstractmethod
    def send(self, obj, dest):
        '''
        Sends objects, mostly of type :class:`.Parcel`, to a replica or master object

        :param obj: object to send
        :type obj: depends

        :param str dest: name of destination object
        '''
        pass

    @abstractmethod
    def recv(self, source):
        '''
        Receives objects, mostly of type :class:`.Parcel`, from a replica or master object

        :return: the received object
        :rtype: depends
        '''
        pass
    
    
