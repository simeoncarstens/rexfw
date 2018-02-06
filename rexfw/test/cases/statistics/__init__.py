'''
'''

from rexfw.statistics import Statistics, REStatistics
from rexfw.test.cases.statistics.writers import MockStatisticsWriter


class MockStatistics(Statistics):

    def __init__(self):

        super(MockStatistics, self).__init__(elements=[],
                                             stats_writer=[MockStatisticsWriter()])

class MockREStatistics(Statistics):

    def __init__(self):

        super(MockREStatistics, self).__init__(elements=[],
                                               stats_writer=[MockStatisticsWriter()])
        
