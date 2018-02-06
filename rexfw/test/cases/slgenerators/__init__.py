'''
'''

from rexfw.slgenerators import AbstractSwapListGenerator, ExchangeParams


class MockSwapListGenerator(AbstractSwapListGenerator):

    def generate_swap_list(self, step):

        return ['replica1', 'replica2', ExchangeParams([],[])]
