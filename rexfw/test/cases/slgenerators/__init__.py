'''
'''

from rexfw.slgenerators import AbstractSwapListGenerator, ExchangeParams
from rexfw.test.cases.proposers.params import MockProposerParams


class MockSwapListGenerator(AbstractSwapListGenerator):

    def generate_swap_list(self, step):

        if step % 2 == 0:
            return [['replica1', 'replica2',
                     ExchangeParams([], MockProposerParams())]]
        else:
            return [['replica2', 'replica3',
                     ExchangeParams([], MockProposerParams())]]
            
