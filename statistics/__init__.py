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

    def __init__(self, elements, stats_writer=[]):

        self._stats_writer = [ConsoleStatisticsWriter] if len(stats_writer) == 0  else stats_writer
        self._elements = FilterableQuantityList(elements)

    def update(self, origins, sampler_stats_list):
        
        for step, sampling_stats in sampler_stats_list:
            self.update_single_step(origins, step, sampling_stats)
        
    def update_single_step(self, origins, step, sampling_stats):

        quantities = self.elements.select(origins=origins)
        for quantity in quantities:
            quantity.update(step, sampling_stats)

    def write_last(self, step):

        for writer in self._stats_writer:
            writer.write(step, self.elements)

    @property
    def elements(self):
        return self._elements


class REStatistics(Statistics):

    def __init__(self, elements, work_elements, heat_elements, 
                 stats_writer=[], works_writer=[], heats_writer=[]):

        super(REStatistics, self).__init__(elements + work_elements + heat_elements, stats_writer)

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
    
    def _init_averages(self, averages):

        self._averages = averages

    # def update(self, step, senders):

    #     elements = self._get_sampling_stats(senders)
    #     data = [self._create_data_from_sample_stats(sampler, stats) for sampler, stats in elements.iteritems()]
    #     data = [y for z in data for y in z]
    #     for d in data:
    #         super(SRSamplingStatistics, self).update(step, *d)
                        
    # def _get_sampling_stats(self, replicas):

    #     results = {}

    #     for r in replicas:
    #         request = SendStatsRequest(self.name)
    #         parcel = Parcel(self.name, r, request)
    #         self._comm.send(parcel, r)

    #     for r in replicas:
    #         results.update(**{'sampler_{}'.format(r): self._comm.recv(source=r).data})

    #     return results


class MCMCSamplingStatistics(SRSamplingStatistics):

    def _create_data_from_sample_stats(self, sampler, stats):

        return [('stepsize', [sampler], stats.stepsize),
                ('mcmc_accepted', [sampler], stats.accepted),
                ('mcmc_p_acc', [sampler], stats.accepted)]


class GibbsSamplingStatistics(SRSamplingStatistics):

    pass
    # def _create_data_from_sample_stats(self, sampler, stats):

    #     # return [('structures_mcmc_p_acc', [sampler], stats['structures'].accepted),
    #     #         ('weights_mcmc_p_acc', [sampler], stats['weights'].accepted)]

    #     res = [('{}_{}'.format(v, field), [sampler],
    #              eval('stats[v].{}'.format(field))) for v in stats.iterkeys()
    #                                             for field in stats[v]._fields]

    #     return [(x.name, [

    #     # print res
    #     return res
