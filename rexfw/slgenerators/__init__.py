'''
Swap list generators generating lists of triples: two replica names and an
:class:`ExchangeParams` object. They tell which replicas should attempt to
swap their states and which parameters to use for the swap
'''

from abc import abstractmethod
from collections import namedtuple

ExchangeParams = namedtuple('ExchangeParams', 'proposers proposer_params')


class AbstractSwapListGenerator(object):
    
    @abstractmethod
    def generate_swap_list(self, step):
        '''
        Creates a list of swaps to be performed at a given sampling step

        :param int step: a sampling step

        :return: a list of lists; the second dimension being of the form
                 ('replica_name1', 'replica_name2', ExchangeParams instance)
        :rtype: list
        '''
        pass

    
class StandardSwapListGenerator(AbstractSwapListGenerator):

    _which = 0
    
    def __init__(self, n_replicas, param_list):
        '''
        Implements the standard swap scheme: 1<>2, 3<>4, ..., then 2<>3, 4<>5, ...
        '''

        self._n_replicas = n_replicas
        self._replica_list = ['replica{}'.format(i) for i in range(1, self._n_replicas + 1)]
        self._proposer_list = ['prop{}'.format(i) for i in range(1, self._n_replicas + 1)]
        self._param_list = param_list
        
    def generate_swap_list(self, step):

        if len(self._replica_list) == 2:
            self._which = 0
        swap_list = list(zip(self._replica_list[self._which::2],
                        self._replica_list[self._which + 1::2],
                        self._param_list[self._which::2]))
        self._which = int(not self._which)

        return swap_list
