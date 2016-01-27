'''
Classes representing runtime-averages of quantities such as acceptance rates
'''

from abc import abstractmethod, ABCMeta

from rexfw.statistics import LoggedQuantity


class AbstractAverage(LoggedQuantity):

    __metaclass__ = ABCMeta
    _name = None
    _default_value = None
    
    def __init__(self, name):

        super(AbstractAverage, self).__init__(name, self._default_value)
        self._n_contributions = 0
        # self._value = self._default_value
        # self._step = None

    @abstractmethod
    def _calculate_new_value(self, info):
        pass
        
    def update(self, info):

        new_value = self._calculate_new_value(info)

        if self.value == self._default_value:
            self.value = new_value
            self._n_contributions += 1
        else:
            self.value *= self._n_contributions / float(self._n_contributions + 1)
            self._n_contributions += 1
            self.value += new_value / float(self._n_contributions)

    @abstractmethod
    def is_relevant(self, quantity):
        pass
    
    @abstractmethod
    def __repr__(self):
        pass


class MCMCAcceptanceRateAverage(AbstractAverage):

    _default_value = 0.0

    def __init__(self, replica):

        super(MCMCAcceptanceRateAverage, self).__init__('mcmc_p_acc')

        self.replica = replica
        self.origins.add(replica)

    def is_relevant(self, quantity):

        return quantity.name == 'mcmc_accepted' and quantity.origins == self.origins
    
    def _calculate_new_value(self, quantity):
        return int(quantity.value)

    def __repr__(self):

        return 'p_acc {}: {:.2f}'.format(self.replica, self.value)

    
class REAcceptanceRateAverage(AbstractAverage):

    _default_value = 0.0

    def __init__(self, replica1, replica2):

        super(REAcceptanceRateAverage, self).__init__('re_p_acc')

        self.replica1, self.replica2 = replica1, replica2
        self.origins.add(replica1)
        self.origins.add(replica2)

    def is_relevant(self, quantity):

        return quantity.name == 're_accepted' and quantity.origins == self.origins
    
    def _calculate_new_value(self, quantity):
        return int(quantity.value)

    def __repr__(self):

        return 'p_acc {} <> {}: {:.2f}'.format(self.replica1, self.replica2, self.value)
