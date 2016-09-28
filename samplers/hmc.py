'''
Compatible HMCSampler
'''

from collections import namedtuple

from csb.statistics.samplers.mc.singlechain import HMCSampler
from fastcode import FastHMCSampler
HMCSampler = FastHMCSampler

HMCSampleStats = namedtuple('HMCSampleStats', 'accepted total stepsize')


class CompatibleHMCSampler(HMCSampler):

    def __init__(self, pdf, state, timestep, nsteps, adapt_timestep=False):

        super(CompatibleHMCSampler, self).__init__(pdf, state, pdf.gradient, timestep, nsteps)

        self.adapt_timestep = adapt_timestep

    @property
    def stepsize(self):
        return self.timestep
        
    def get_last_draw_stats(self):
        
        return HMCSampleStats(self._last_move_accepted, self._nmoves, self.timestep)

    def sample(self):

        res = super(CompatibleHMCSampler, self).sample()

        if self.adapt_timestep:
            if self.last_move_accepted:
                self.timestep *= 1.05
            else:
                self.timestep *= 0.95

        return res