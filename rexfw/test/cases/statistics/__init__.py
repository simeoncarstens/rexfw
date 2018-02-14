'''
'''

from collections import deque

from rexfw.statistics import Statistics, REStatistics
from rexfw.test.cases.statistics.writers import MockStatisticsWriter


class MockStatistics(Statistics):

    def __init__(self):

        super(MockStatistics, self).__init__(elements=[],
                                             stats_writer=[MockStatisticsWriter()])

        self.update_stack = deque()
        self.write_stack = deque()

    def update(self, origins, sampler_stats_list):

        self.update_stack.append((sampler_stats_list, origins))

    def write_last(self, step):

        self.write_stack.append(step)
        

class MockREStatistics(Statistics):

    def __init__(self):

        super(MockREStatistics, self).__init__(elements=[],
                                               stats_writer=[MockStatisticsWriter()])

        self.write_stack = deque()

    def write_last(self, step):

        self.write_stack.append(step)
        
