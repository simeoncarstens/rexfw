'''
Classes representing runtime-averages of quantities such as acceptance rates
'''

from abc import abstractmethod

from rexfw.statistics.logged_quantities import LoggedQuantity


class AbstractAverage(LoggedQuantity):
    
    def __init__(self, origins, stats_fields, name, variable_name=None):

        super(AbstractAverage, self).__init__(origins, stats_fields, name, variable_name)
        self._n_contributions = 0
        self._untouched = True

    @abstractmethod
    def _calculate_new_value(self, info):
        '''
        Calculates a new average value from the information given in info
        '''
        pass
        
    def update(self, step, stats):

        new_value = self._calculate_new_value(stats)
        if self._untouched:
            self._values.update(**{str(step): new_value})
            self._n_contributions += 1
            self._untouched = False
        else:
            ## calculates average from previous average and new information
            new = self.current_value * self._n_contributions / float(self._n_contributions + 1)
            self._n_contributions += 1
            new += new_value / float(self._n_contributions)
            self._values.update(**{str(step): new})


class MCMCAcceptanceRateAverage(AbstractAverage):

    def __init__(self, replica, variable_name):

        super(MCMCAcceptanceRateAverage, self).__init__([replica],
                                                        ['accepted'], 
                                                        'acceptance rate',
                                                        variable_name)

        self._default_value = 0.0
    
    def _calculate_new_value(self, stats):
        
        return float(stats[self.variable_name].accepted)

    def __repr__(self):

        return 'p_acc {} {}: {:.2f}'.format(self.variable_name, self.origins[0],
                                            self.current_value)

    
class REAcceptanceRateAverage(AbstractAverage):

    def __init__(self, replica1, replica2):

        super(REAcceptanceRateAverage, self).__init__([replica1, replica2],
                                                      ['accepted'],
                                                      'acceptance rate')

        self._default_value = 0.0

    def _calculate_new_value(self, stats):
        return float(stats.accepted)

    def __repr__(self):

        return 'p_acc {} <> {}: {:.2f}'.format(self.origins[0], self.origins[1], self.current_value)
