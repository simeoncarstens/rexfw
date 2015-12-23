'''
StatisticsWriter classes which... well... write statistics to stdout / files / ...
'''


class AbstractStatisticsWriter(object):

    _outstream = None

    def write(self, elements, fields):

        pass

class ConsoleStatisticsWriter(AbstractStatisticsWriter):

    def write(self, elements, fields):

        for x in elements:
            for k in x.iterkeys():
                if k in fields:
                    print x[k],
            print
