'''
'''

from rexfw.statistics.writers import AbstractStatisticsWriter


class MockStatisticsWriter(AbstractStatisticsWriter):

    def __init__(self):

        super(MockStatisticsWriter, self).__init__('8-)')

    def write(self, step, elements):
        pass
