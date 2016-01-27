'''
Statistics classes responsible for tracking sampling statistics
'''

from abc import ABCMeta, abstractmethod, abstractproperty

from collections import defaultdict

from rexfw import Parcel
from rexfw.statistics.writers import ConsoleStatisticsWriter
from rexfw.statistics.requests import SendStatsRequest

class FilterableQuantityList(list):

    def select(self, **kwargs):

        criterion = lambda x: sum([x.__getattribute__(k) == v 
                                   for k, v in kwargs.iteritems() if hasattr(x, k)]) == len(kwargs)
        # criterion = lambda x: sum([x.__dict__[k]==v for k,v in kwargs.items() if k in x.__dict__]) == len(kwargs)

        # return self
        
        return self.__class__((filter(criterion, self)))
    

class LoggedQuantity(object):

    def __init__(self, name, value):

        self.step = None
        self._name = name
        self._value = value
        self.origins = set()

    @property
    def name(self):
        return self._name

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value


class SamplerStepsize(LoggedQuantity):

    def __init__(self, value, sampler_name):

        super(SamplerStepsize, self).__init__('stepsize', value)
        self.origins.add(sampler_name)

    def __repr__(self):

        return 'stepsize {}: {}'.format(list(self.origins)[0], self.value)
        

class MCMCMoveAccepted(LoggedQuantity):

    def __init__(self, value, sampler_name):

        super(MCMCMoveAccepted, self).__init__('mcmc_accepted', value)
        self.origins.add(sampler_name)

    def __repr__(self):

        return 'accepted {}: {}'.format(list(self.origins)[0], self.value)


class REMoveAccepted(LoggedQuantity):

    def __init__(self, value, replica1, replica2):

        super(REMoveAccepted, self).__init__('re_accepted', value)
        self.origins.add(replica1)
        self.origins.add(replica2)
    
    def __repr__(self):

        return 'accepted {} <> {}: {}'.format(sorted(list(self.origins))[0], sorted(list(self.origins))[1], 
                                              self.value)

class REWorks(LoggedQuantity):

    def __init__(self, value, replica1, replica2):

        super(REWorks, self).__init__('works', value)
        self.origins.add(replica1)
        self.origins.add(replica2)
    
    def __repr__(self):

        return 'works {} <> {}: {}'.format(sorted(list(self.origins))[0], sorted(list(self.origins))[1], 
                                           self.value)
    
    
class Statistics(object):

    _elements = defaultdict(FilterableQuantityList)
    _averages = FilterableQuantityList()

    def __init__(self, name, averages=[], stats_writer=None):

        self.name = name
        self._stats_writer = ConsoleStatisticsWriter if stats_writer is None else stats_writer
        self._averages = averages
        self._init_averages(averages)

    def initialize(self, replica_names):

        self._n_replicas = len(replica_names)
        self._replica_names = replica_names
        
    def _init_averages(self, averages):

        self._averages = FilterableQuantityList(averages)
        
    def update(self, step, quantity):

        quantity.step=step
        self._elements['step{}'.format(step)].append(quantity)
        self._update_averages(step, quantity)

    def _update_averages(self, step, quantity):

        for avg in self._averages:
            if avg.is_relevant(quantity):
                avg.update(quantity)

    def write(self, step, elements=None):

        self._stats_writer.write(step, self._elements[elements], fields)

    def write_averages(self, step, which=None):

        # self._stats_writer.write(step, [self.averages], which)

        pass
        # if names is None:
        #     names = self._averages.keys()

        # self._stats_writer.write(step, 
        #                          [{k: v for k, v in self._averages.iteritems()
        #                                 if k in names}],
        #                          names)

    @property
    def averages(self):
        return self._averages

    @property
    def elements(self):
        return self._elements


class SRSamplingStatistics(Statistics):

    def __init__(self, name, comm, averages={}, stats_writer=None):

        super(SRSamplingStatistics, self).__init__(name, averages, stats_writer)

        self._comm = comm
    
    def _init_averages(self, averages):

        self._averages = averages

    def update(self, step, senders):

        elements = self._get_sampling_stats(senders)
        for sampler, stats in elements.iteritems():
            quantities = self._create_quantities_from_sample_stats(sampler, stats)
            for q in quantities:
                super(SRSamplingStatistics, self).update(step, q)
                        
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

    def __init__(self, comm, name='MCMCStats0', averages={}, stats_writer=None):

        super(MCMCSamplingStatistics, self).__init__(name, comm, averages, stats_writer)

    def _create_quantities_from_sample_stats(self, sampler, stats):

        return {MCMCMoveAccepted(stats.accepted, sampler), SamplerStepsize(stats.stepsize, sampler)}
    
