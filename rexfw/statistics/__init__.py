'''
Statistics classes responsible for tracking sampling statistics
'''

from abc import ABCMeta, abstractmethod, abstractproperty

from rexfw import Parcel
from rexfw.statistics.writers import ConsoleStatisticsWriter


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
            quantities_to_write = [e for e in self.elements
                                   if e.name in writer.quantities_to_write]
            quantities_to_write = FilterableQuantityList(quantities_to_write)
            writer.write(step, quantities_to_write)

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
