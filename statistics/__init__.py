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

    def __init__(self, name, elements, stats_writer=[]):

        self.name = name
        self._stats_writer = [ConsoleStatisticsWriter] if len(stats_writer) == 0  else stats_writer
        self._elements = FilterableQuantityList(elements)
        
    def update(self, step, name, origins, value):

        quantities = self.elements.select(origins=origins, name=name)
        for quantity in quantities:
            quantity.update(step, value)

    def write_last(self, step):

        for writer in self._stats_writer:
            writer.write(step, self.elements)

    @property
    def elements(self):
        return self._elements


class REStatistics(Statistics):

    def __init__(self, elements, work_elements, heat_elements, 
                 name='REStats0', stats_writer=[], 
                 works_writer=[], heats_writer=[]):

        super(REStatistics, self).__init__(name, elements + work_elements + heat_elements, stats_writer)

        self._work_elements = FilterableQuantityList(work_elements)
        self._heat_elements = FilterableQuantityList(heat_elements)
        self._works_writer = works_writer
        self._heats_writer = heats_writer
        
    def write_last(self, step):

        super(REStatistics, self).write_last(step)
        
        self._write_works()
        self._write_heats()

    def _write_works(self):

        for writer in self._works_writer:
            writer.write(self._work_elements)    

    def _write_heats(self):

        for writer in self._heats_writer:
            writer.write(self._heat_elements)    

            
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

        return [('stepsize', [sampler], stats.stepsize),
                ('mcmc_accepted', [sampler], stats.accepted),
                ('mcmc_p_acc', [sampler], stats.accepted)]
