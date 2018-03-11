'''
Defines the interface for proposer classes which propose states
for RE, RENS, ... swaps
'''

import numpy

from abc import ABCMeta, abstractmethod

from csb.statistics.samplers import State
import csb.statistics.samplers.mc.neqsteppropagator as noneqprops

from rexfw import Parcel


class GeneralTrajectory(list):

    def __init__(self, items, work=0.0, heat=0.0):

        super(GeneralTrajectory, self).__init__(items)

        self.work = work
        self.heat = heat
        
        
class AbstractProposer(object):

    __metaclass__ = ABCMeta

    def __init__(self, name):

        self.name = name

    @abstractmethod
    def propose(self, local_replica, partner_state, partner_energy, params):
        pass


