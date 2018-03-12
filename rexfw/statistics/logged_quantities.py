'''
Logable (?) quantities
'''

from collections import OrderedDict


class LoggedQuantity(object):

    def __init__(self, origins, stats_fields, name, variable_name=None):
        '''
        Base class representing sampling quantities which can be tracked by
        :class:`.Statistics` instances and written by :class:`.AbstractStatisticsWriter`
        instances

        :param origins: list of object (mostly, replica) names which give rise to this
                        quantity; e.g., replica1 and replica2 for the acceptance rate
                        for swaps between those two replicas
        :type origins: list of str

        :param stats_fields: the attribute names that will be looked up in 
                             small sampling statistics objects to calculate the value
                             of the quantity
        :type stats_fields: list of str

        :param str name: the name of the logged quantity, e.g., 'accepance rate'

        :param str variable_name: the name of the sampled variable associated with this quantity
        '''
        self._values = OrderedDict()
        self._default_value = None
        self.step = None
        self.origins = origins
        self.stats_fields = stats_fields
        self.name = name
        self.variable_name = variable_name

    def __getitem__(self, step):
        '''
        Gets the value for the logged quantity for a given step

        :return: a value of the logged quantity
        :rtype: depends on the quantity
        '''
        return self.values[str(step)] if step != -1 else self.current_value

    @property
    def values(self):
        '''
        Returns all stored values of the logged quantity
        '''
        return self._values

    @property
    def current_value(self):
        '''
        Returns the current (last) value of the logged quantity
        '''
        if len(self.values) > 0:
            return self.values[next(reversed(self.values))]
        else:    
            return self._default_value

    def _get_value(self, stats):
        '''
        Retrieves a value for the logged quantity from a small sampling statistics object

        :param stats: dict of the form {variable_name: SamplingStats}
        :type stats: dict
        '''
        pass
    
    def update(self, step, stats):
        '''
        Stores sampling statistics for a given step

        :param int step: the sampling step during which the statistics in stats where
                         created

        :param stats: dict of the form {variable_name: SamplingStats}
        :type stats: dict
        '''
        self._values.update(**{str(step): self._get_value(stats)})


class SamplerStepsize(LoggedQuantity):

    def __init__(self, replica, variable_name):
        '''
        Logged quantity which tracks MCMC sampler step sizes

        :param str replica: the name of the replica in which the sampler with these
                            step sizes lives
        :param str variable_name: the name of the sampling variable associated with the
                                  step size
        '''

        super(SamplerStepsize, self).__init__([replica], ['stepsize'], 'stepsize',
                                              variable_name)

    def _get_value(self, stats):
        
        return stats[self.variable_name].stepsize

    def __repr__(self):

        return '{} {} {}: {}'.format(self.origins[0], self.variable_name, 
                                     self.name,self.current_value)
        

class REWorks(LoggedQuantity):

    def __init__(self, replica1, replica2):
        '''
        Keeps track of works expended during replica exchange swap trajectories

        :param str replica1: name of first involved replica
        :param str replica2: name of second involved replica
        '''

        import numpy 
        
        super(REWorks, self).__init__([replica1, replica2], ['works'], 'works')
        self._default_value = numpy.array([0.0,0.0])

    def _get_value(self, stats):

        return stats.works
    
    def __repr__(self):

        return '{} {} <> {}: {}'.format(self.name, self.origins[0], self.origins[1], 
                                        self.current_value)

    
class REHeats(LoggedQuantity):

    def __init__(self, replica1, replica2):
        '''
        Keeps track of heats produced during replica exchange swap trajectories

        :param str replica1: name of first involved replica
        :param str replica2: name of second involved replica
        '''

        import numpy 
        
        super(REHeats, self).__init__([replica1, replica2], ['heats'], 'heats')
        self._default_value = numpy.array([0.0,0.0])
    
    def _get_value(self, stats):

        return stats.heats

    def __repr__(self):

        return '{} {} <> {}: {}'.format(self.name, self.origins[0], self.origins[1], 
                                        self.current_value)
