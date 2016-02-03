'''
Classes representing runtime-averages of quantities such as acceptance rates
'''

from abc import abstractmethod, ABCMeta

from rexfw.statistics.logged_quantities import LoggedQuantity


class AbstractAverage(LoggedQuantity):

    __metaclass__ = ABCMeta
    
    def __init__(self, name):

        super(AbstractAverage, self).__init__(name)
        self._n_contributions = 0
        self._untouched = True

    @abstractmethod
    def _calculate_new_value(self, info):
        pass
        
    def update(self, step, value):

        new_value = self._calculate_new_value(value)

        if self._untouched:
            self._values.update(**{str(step): new_value})
            self._n_contributions += 1
            self._untouched = False
        else:
            new = self.current_value * self._n_contributions / float(self._n_contributions + 1)
            # self.value *= self._n_contributions / float(self._n_contributions + 1)
            self._n_contributions += 1
            # self.value += new_value / float(self._n_contributions)
            new += new_value / float(self._n_contributions)
            self._values.update(**{str(step): new})

    # @abstractmethod
    # def __repr__(self):
    #     pass


class MCMCAcceptanceRateAverage(AbstractAverage):

    def __init__(self, replica):

        super(MCMCAcceptanceRateAverage, self).__init__('mcmc_p_acc')

        self.replica = replica
        self.origins.append(replica)
        self._default_value = 0.0
    
    def _calculate_new_value(self, value):
        return float(value)

    def __repr__(self):

        return 'p_acc {}: {:.2f}'.format(self.replica, self.current_value)

    
class REAcceptanceRateAverage(AbstractAverage):

    def __init__(self, replica1, replica2):

        super(REAcceptanceRateAverage, self).__init__('re_p_acc')

        self.replica1, self.replica2 = replica1, replica2
        self.origins.append(replica1)
        self.origins.append(replica2)
        self._default_value = 0.0

    def _calculate_new_value(self, value):
        return float(value)

    def __repr__(self):

        return 'p_acc {} <> {}: {:.2f}'.format(self.replica1, self.replica2, self.current_value)
