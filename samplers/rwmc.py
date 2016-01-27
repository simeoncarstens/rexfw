'''
Compatible RWMCSampler
'''

from collections import namedtuple

from csb.statistics.samplers.mc.singlechain import RWMCSampler


RWMCSampleStats = namedtuple('RWMCSampleStats', 'accepted total stepsize')


class CompatibleRWMCSampler(RWMCSampler):

    def get_last_draw_stats(self):
        
        return RWMCSampleStats(self._last_move_accepted, self._nmoves, self.stepsize)

    # def sample(self):
    #     import numpy
    #     from csb.statistics.samplers import State
    #     self._last_move_accepted = True
    #     return State(numpy.array([2.0]))
