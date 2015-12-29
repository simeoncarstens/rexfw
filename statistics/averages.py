'''
Classes representing runtime-averages of quantities such as acceptance rates
'''

from abc import abstractmethod, ABCMeta

class AbstractAverage(object):

    __metaclass__ = ABCMeta
    _required_field_names = None
    _name = None
    
    def __init__(self):

        self._n_contributions = 0
        self._value = None
        self._step = None

    @abstractmethod
    def _calculate_new_value(self, info):
        pass
        
    def update(self, step, info):

        new_value = self._calculate_new_value(info)

        if self._value is None:
            self._value = new_value
            self._n_contributions += 1
        else:
            self._value *= self._n_contributions / float(self._n_contributions + 1)
            self._n_contributions += 1
            self._value += new_value / float(self._n_contributions)

    @property
    def required_field_names(self):
        return self._required_field_names

    @property
    def name(self):
        return self._name

    @property
    def value(self):
        return self._value

    def __repr__(self):

        return str(self._value)
    
class AcceptanceRateAverage(AbstractAverage):

    _required_field_names = ('accepted',)
    _name = 'p_acc'
    
    def _calculate_new_value(self, info):
        return int(info.accepted)
