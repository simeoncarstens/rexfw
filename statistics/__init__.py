'''
Statistics classes responsible for tracking sampling statistics
'''

from abc import ABCMeta, abstractmethod, abstractproperty

from rexfw import Parcel
from rexfw.statistics.writers import ConsoleStatisticsWriter
from rexfw.statistics.requests import SendStatsRequest

class FilterableQuantityList(list):

    def select(self, **kwargs):

        criterion = lambda x: sum([x.__getattribute__(k) == v 
                                   for k, v in kwargs.iteritems() if hasattr(x, k)]) == len(kwargs)
        
        return self.__class__(filter(criterion, self))

        
class Statistics(object):

    _elements = FilterableQuantityList()

    def __init__(self, name, elements, stats_writer=None):

        self.name = name
        self._stats_writer = ConsoleStatisticsWriter if stats_writer is None else stats_writer
        self._elements = FilterableQuantityList(elements)

    def initialize(self, replica_names):

        self._n_replicas = len(replica_names)
        self._replica_names = replica_names
        
    def update(self, step, name, origins, value):

        quantities = self.elements.select(origins=origins, name=name)
        for quantity in quantities:
            quantity.update(step, value)

    def write_last(self, step):

        for writer in self._stats_writer:
            writer.write(step, FilterableQuantityList(self.elements))

    @property
    def elements(self):
        return self._elements


class SRSamplingStatistics(Statistics):

    def __init__(self, name, comm, elements, stats_writer=None):

        super(SRSamplingStatistics, self).__init__(name, elements, stats_writer)

        self._comm = comm
    
    def _init_averages(self, averages):

        self._averages = averages

    def update(self, step, senders):

        elements = self._get_sampling_stats(senders)
        data = [self._create_data_from_sample_stats(sampler, stats) for sampler, stats in elements.iteritems()]
        data = [y for z in data for y in z]
        for d in data:
            super(SRSamplingStatistics, self).update(step, *d)
                        
    def _get_sampling_stats(self, replicas):

        results = {}

        for r in replicas:
            request = SendStatsRequest(self.name)
            parcel = Parcel(self.name, r, request)
            self._comm.send(parcel, r)

        for r in replicas:
            results.update(**{'sampler_{}'.format(r): self._comm.recv(source=r).data})

        return results


class MCMCSamplingStatistics(SRSamplingStatistics):

    def __init__(self, comm, elements, name='MCMCStats0', stats_writer=None):

        super(MCMCSamplingStatistics, self).__init__(name, comm, elements, stats_writer)

    def _create_data_from_sample_stats(self, sampler, stats):

        return [('stepsize', {sampler}, stats.stepsize),
                ('mcmc_accepted', {sampler}, stats.accepted),
                ('mcmc_p_acc', {sampler}, stats.accepted)]
