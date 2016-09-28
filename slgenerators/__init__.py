'''
Swap list generators
'''

from abc import ABCMeta, abstractmethod
from collections import namedtuple

ExchangeParams = namedtuple('ExchangeParams', 'proposers proposer_params')


class AbstractSwapListGenerator(object):

    __metaclass__ = ABCMeta
    
    @abstractmethod
    def generate_swap_list(self, step):
        pass

    
class StandardSwapListGenerator(AbstractSwapListGenerator):

    _which = 0
    
    def __init__(self, n_replicas, param_list):

        self._n_replicas = n_replicas
        self._replica_list = ['replica{}'.format(i) for i in range(1, self._n_replicas + 1)]
        self._proposer_list = ['prop{}'.format(i) for i in range(1, self._n_replicas + 1)]
        self._param_list = param_list
        
    def generate_swap_list(self, step):

        if len(self._replica_list) == 2:
            self._which = 0
        swap_list = zip(self._replica_list[self._which::2],
                        self._replica_list[self._which + 1::2],
                        self._param_list[self._which::2])
        self._which = int(not self._which)

        return swap_list
