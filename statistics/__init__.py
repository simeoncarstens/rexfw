'''
Statistics classes responsible for tracking sampling statistics
'''

from abc import ABCMeta, abstractmethod, abstractproperty

from rexfw import Parcel
from rexfw.statistics.writers import ConsoleStatisticsWriter
from rexfw.statistics.requests import SendStatsRequest


class Statistics(object):

    _elements = []

    def __init__(self, name, averages=[], stats_writer=None):

        self.name = name
        self._stats_writer = ConsoleStatisticsWriter if stats_writer is None else stats_writer
        self._averages = averages
        self._init_averages(averages)

    def initialize(self, replica_names):

        self._n_replicas = len(replica_names)
        self._replica_names = replica_names
        
    def _init_averages(self, averages):

        pass
    
    def update(self, step, element):

        self._elements.append(element)
        self._update_averages(step, element)

    def _update_averages(self, step, info):

        for avg in self._averages:
            if avg.field_name in info:
                avg.update(step, info[avg.field_name])

    def write(self, elements=None, fields=None):

        self._stats_writer.write(self._elements[elements], fields)

    @property
    def averages(self):
        return self._averages

    @property
    def elements(self):
        return self._elements


class MCMCSamplingStatistics(Statistics):

    _elements = []

    def __init__(self, comm, name='MCMCStats0', averages={}, stats_writer=None):

        super(MCMCSamplingStatistics, self).__init__(name, averages, stats_writer)

        self._comm = comm
    
    def _init_averages(self, averages):

        if averages is None:
            
            from rexfw.statistics.averages import AcceptanceRateAverage
            
            self._averages.update(**{'sampler{}'.format(i): {'p_acc': AcceptanceRateAverage()}
                                     for i in xrange(1,self._n_replicas + 1)})
        else:
            self._averages.update(**averages)

    def update(self, step, senders):

        element = self._get_sampling_stats(senders)
        element.update(step=step)
        self._elements.append(element)
        self._update_averages(step, element)
    
    def _get_sampling_stats(self, replicas):

        results = {}

        for r in replicas:
            request = SendStatsRequest(self.name)
            parcel = Parcel(self.name, r, request)
            self._comm.send(parcel, r)

        for r in replicas:
            results.update(**{'sampler_{}'.format(r): self._comm.recv(source=r).data})

        return results
            
    def _update_averages(self, step, info):

        for key in info.iterkeys():
            if key == 'step':
                continue
            sampler_stats = self._averages[key]
            for avg in sampler_stats.iterkeys():
                if set(sampler_stats[avg].required_field_names).issubset(set(info[key]._fields)):
                    sampler_stats[avg].update(step, info[key])


class REStatistics(Statistics):

    def __init__(self, name='REStats0', averages={}, stats_writer=None):

        super(REStatistics, self).__init__(name, averages, stats_writer)

    def _update_averages(self, step, info):

        for key in info.iterkeys():
            if key == 'step':
                continue
            ex_stats = self._averages[key]
            for avg in ex_stats.iterkeys():
                if set(ex_stats[avg].required_field_names).issubset(set(info[key]._fields)):
                    ex_stats[avg].update(step, info[key])
