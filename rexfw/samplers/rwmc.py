'''
A Metropolis-Hastings sampler as an example for the sampler interface
'''

import numpy as np
from collections import namedtuple

from rexfw.samplers import AbstractSampler


RWMCSampleStats = namedtuple('RWMCSampleStats', 'accepted total stepsize')


class RWMCSampler(AbstractSampler):

    def __init__(self, pdf, state, stepsize, variable_name='x'):

        super(RWMCSampler, self).__init__(pdf, state, variable_name)
        
        self.stepsize = stepsize
        self._last_move_accepted = False
        self._n_moves = 0

    @property
    def last_draw_stats(self):
        
        return {self.variable_name: RWMCSampleStats(self._last_move_accepted, 
                                                    self._n_moves, self.stepsize)}

    def sample(self):

        E_old = -self.pdf.log_prob(self.state)
        proposal = self.state + np.random.uniform(low=-self.stepsize, high=self.stepsize)
        E_new = -self.pdf.log_prob(proposal)

        accepted = np.random.random() < np.exp(-(E_new - E_old))

        if accepted:
            self.state = proposal
            self._last_move_accepted = True
        else:
            self._last_move_accepted = False

        self._n_moves += 1

        return self.state
