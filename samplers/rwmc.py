'''
Compatible RWMCSampler
'''

from collections import namedtuple

from csb.statistics.samplers.mc.singlechain import RWMCSampler


RWMCSampleStats = namedtuple('RWMCSampleStats', 'accepted total')


class CompatibleRWMCSampler(RWMCSampler):

    def get_last_draw_stats(self):
        
        return RWMCSampleStats(self._last_move_accepted, self._nmoves)
