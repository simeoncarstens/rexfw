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
        '''
        A very simple list-like object which represents a trajectory
        or sequence of states

        :param iterable items: the sequence of states making up the trajectory
        :param float work: the work expended during the trajectory (needed for
                           acceptance criterion)
        :param float heat: the heat produced during the trajectory (needed for
                           acceptance criterion in some RENS implementations)
        '''

        super(GeneralTrajectory, self).__init__(items)

        self.work = work
        self.heat = heat
        
        
class AbstractProposer(object):

    __metaclass__ = ABCMeta

    def __init__(self, name):
        '''
        A class exposing the interface proposers need
        '''
    
        self.name = name

    @abstractmethod
    def propose(self, local_replica, partner_state, partner_energy, params):
        '''
        Calculates a proposal using information from the replica, the exchange partner
        state and energy, and possibly other information stored in params

        :param :class:`.Replica` local_replica: the replica which is supposed to propose a state

        :param partner_state: the state of the exchange partner
        :type partner_state: depends on you

        :param partner_energy: the exchange partner's current energy
        :type partner_energy: depends on you

        :param :class:`.AbstractProposerParams` params: parameters the proposer may need
                                                        to calculate a proposal
        '''
        pass


