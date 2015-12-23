'''
Statistics classes responsible for tracking sampling statistics
'''

from abc import ABCMeta, abstractmethod, abstractproperty

from rexfw.statistics.writers import ConsoleStatisticsWriter


class Statistics(object):

    _averages = []
    _elements = []

    def __init__(self, n_replicas, comm, averages=[], stats_writer=None):

        self._n_replicas = n_replicas
        self._comm = comm
        self._stats_writer = ConsoleStatisticsWriter if stats_writer is None else stats_writer

        self._init_averages(averages)

    def _init_averages(self, averages):
        
        for avg in averages:
            self._averages.append(avg)

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

    _averages = {}
    _elements = []

    def __init__(self, n_replicas, comm, averages=None, stats_writer=None):

        super(MCMCSamplingStatistics, self).__init__(n_replicas, comm, averages, stats_writer)
    
    def _init_averages(self, averages):

        if averages is None:
            
            from rexfw.statistics.averages import AcceptanceRateAverage
            
            self._averages.update(**{'sampler{}'.format(i): {'p_acc': AcceptanceRateAverage()}
                                     for i in xrange(1,self._n_replicas + 1)})
        else:
            self._averages.update(**averages)

    def update(self, step, senders=None):

        element = self._receive_sampling_stats(senders)
        element.update(step=step)
        self._elements.append(element)
        self._update_averages(step, element)
    
    def _receive_sampling_stats(self, senders=None):

        if not senders is None:
            raise NotImplementedError
        senders = xrange(1, self._n_replicas + 1) if senders == None else senders
        results = {}
        
        for i in senders:
            results.update(**{'sampler{}'.format(i): self._comm.recv(source=i).data})

        return results
            
    def _update_averages(self, step, info):

        for key in info.iterkeys():
            if key == 'step':
                continue
            sampler_stats = self._averages[key]
            for avg in sampler_stats.iterkeys():
                if set(sampler_stats[avg].required_field_names).issubset(set(info[key]._fields)):
                    sampler_stats[avg].update(step, info[key])

# class MCMCSamplingStatistics(SamplingStatistics):

    
