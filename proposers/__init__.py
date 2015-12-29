'''
Proposer classes which propose states for RE, RENS, ... swaps
'''

from abc import ABCMeta, abstractmethod

from rexfw import Parcel

class GeneralTrajectory(list):

    def __init__(self, items, work=0.0, heat=0.0):

        super(GeneralTrajectory, self).__init__(items)

        self.work = work
        self.heat = heat
        
        
class AbstractProposer(object):

    __metaclass__ = ABCMeta

    def __init__(self, name, comm):

        self.name = name
        self._comm = comm

    @abstractmethod
    def propose(self, local_replica, partner_state, partner_energy, params):
        pass


class REProposer(AbstractProposer):

    def propose(self, local_replica, partner_state, partner_energy, params):

        work =   local_replica.get_energy(partner_state) \
               - partner_energy

        return GeneralTrajectory([partner_state, partner_state], work=work)
