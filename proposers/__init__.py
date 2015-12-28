'''
Proposer classes which propose states for RE, RENS, ... swaps
'''

from abc import ABCMeta, abstractmethod

from rexfw import Parcel
from rexfw.proposers.requests import GetEnergyRequest


class AbstractProposer(object):

    __metaclass__ = ABCMeta

    def __init__(self, name, comm):

        self.name = name
        self._comm = comm

    @abstractmethod
    def calculate_proposal(self, local_replica, partner_name, direction, params):
        pass


class AbstractREProposer(AbstractProposer):

    def calculate_proposal(self, local_replica, partner_name, direction, params):
        
        if direction == 'fw':
            work =   self._get_partner_energy(partner_name, local_replica.state) \
                   - local_replica.energy()
            return GeneralTrajectory(local_replica.state, partner_state, work=work)
        if direction == 'rv':
            work =   local_replica.get_energy(partner_state) \
                   - self._get_partner_energy(partner_name)
            return GeneralTrajectory(partner_state, local_replica.state, work=work)

    @abstractmethod
    def _get_partner_energy(self, partner_name, state=None):
        pass
    

class GeneralREProposer(AbstractREProposer):
    
    def _get_partner_energy(self, partner_name, state=None):

        parcel = Parcel(self.name, partner_name, GetEnergyRequest(self.name, state))
        self._comm.send(parcel, partner_name)

        return self._comm.recv(source=partner_name).data 
