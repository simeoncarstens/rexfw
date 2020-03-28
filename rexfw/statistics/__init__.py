'''
Statistics classes responsible for tracking sampling statistics
'''

from abc import abstractmethod, abstractproperty

from rexfw import Parcel
from rexfw.statistics.writers import ConsoleStatisticsWriter


class FilterableQuantityList(list):

    def select(self, **kwargs):
        '''
        A list which allows the user to select only elements whose attributes
        have certain values

        :params dict kwargs: keyword arguments of the form attribute=value
        :return: a list containing the subset of elements with matching attribute values
        :rtype: list
        '''

        criterion = lambda x: sum([x.__getattribute__(k) == v 
                                   for k, v in kwargs.items() if hasattr(x, k)]) == len(kwargs)
        
        return self.__class__(list(filter(criterion, self)))

        
class Statistics(object):

    def __init__(self, elements, stats_writer=[]):
        '''
        A class whose responsibility is to keep track of any kind of sampling statistics

        :param elements: a list of :class:`.LoggedQuantity` objects to keep track of
        :type elements: list of :class:`.LoggedQuantity`
        :param stats_writer: a list of :class:`.AbstractStatisticsWriter` objects which write
                             sampling statistics to the standard output or files or elsewhere
        :type stats_writer: list of :class:`.AbstractStatisticsWriter`
        '''
        self._stats_writer = [ConsoleStatisticsWriter] if len(stats_writer) == 0 else stats_writer
        self._elements = FilterableQuantityList(elements)
 
    def update(self, origins, sampler_stats_list):
        '''
        Updates sampling stats stemming from the replicas in origins with the sampling
        statistics in sampler_stats_list

        :param origins: a list of object (usually, replica) names which gave
                        rise to the sampling stats in sampler_stats_list
        :type origins: list of str

        :param sampler_stats_list: a list of sampler statistics (c.f. the samplers submodule)
                                   to update quantities from
        :type sampler_stats_list: list of sampler statistic objects
        '''
        for step, sampling_stats in sampler_stats_list:
            self.update_single_step(origins, step, sampling_stats)
        
    def update_single_step(self, origins, step, sampling_stats):
        '''
        Updates sampling statistics for a single sampling step

        :param origins: a list of object (usually, replica) names which gave
                        rise to the sampling stats in sampler_stats_list
        :type origins: list of str

        :param int step: the sampling step during which the statistic objects in
                         sampling_stats have been created

        :param sampling_stats: a list of sampler statistics (c.f. the samplers submodule)
                               to update quantities from
        :type sampling_stats: list of sampler statistic objects        
        
        '''        
        quantities = self.elements.select(origins=origins)
        for quantity in quantities:
            quantity.update(step, sampling_stats)

    def write_last(self, step):
        '''
        Probably writes most up-to-date sampling statistics and labels them with
        a certain sampling step

        :param int step: the sampling step for which to write the statistics
        '''
        for writer in self._stats_writer:
            quantities_to_write = [e for e in self.elements
                                   if e.name in writer.quantities_to_write]
            quantities_to_write = FilterableQuantityList(quantities_to_write)
            writer.write(step, quantities_to_write)

    @property
    def elements(self):
        '''
        Returns all quantities which this object is keeping track of

        :return: this object's quantities
        :rtype: list of :class:`.LoggedQuantity` objects
        '''
        return self._elements


class REStatistics(Statistics):

    def __init__(self, elements, work_elements, heat_elements, 
                 stats_writer=[], works_writer=[], heats_writer=[]):
        '''
        This class keeps track of replica exchange swap statistics

        :param elements: a list of :class:`.LoggedQuantity` objects to keep track of
        :type elements: list of :class:`.LoggedQuantity`

        :param work_elements: a list of , e.g., :class:`.REWorks` objects which represent
                              the works expended during a swap trajectory simulation
        :type work_elements: list of :class:`.LoggedQuantity`

        :param heat_elements: a list of, e.g., :class:`.REHeats` objects which represent
                              the heats produced during a swap trajectory simulation
        :type heat_elements: list of :class:`.LoggedQuantity`

        :param stats_writer: a list of :class:`.AbstractStatisticsWriter` objects which write
                             sampling statistics to the standard output or files or elsewhere
        :type stats_writer: list of :class:`.AbstractStatisticsWriter`

        :param works_writer: a list of, e.g., :class:`.StandardFileREWorksStatisticsWriter` objects 
                             which write works to the standard output or files or elsewhere
        :type works_writer: list of :class:`.AbstractStatisticsWriter`
        :param heats_writer: a list of, e.g., :class:`.StandardFileREHeatsStatisticsWriter` objects
                             which write works to the standard output or files or elsewhere
        :type heats_writer: list of :class:`.AbstractStatisticsWriter`

        '''
        super(REStatistics, self).__init__(elements + work_elements + heat_elements, stats_writer)

        self._work_elements = FilterableQuantityList(work_elements)
        self._heat_elements = FilterableQuantityList(heat_elements)
        self._works_writer = works_writer
        self._heats_writer = heats_writer
        
    def write_last(self, step):
        '''
        Makes the writers write works and heats for a given sampling step
        '''

        super(REStatistics, self).write_last(step)
        
        self._write_works()
        self._write_heats()

    def _write_works(self):
        '''
        Makes the work writers write works
        '''
        for writer in self._works_writer:
            writer.write(self._work_elements)    

    def _write_heats(self):
        '''
        Makes the heat writers write heats
        '''
        for writer in self._heats_writer:
            writer.write(self._heat_elements)    
