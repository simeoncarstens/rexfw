'''
Requests masters can send
'''

from collections import namedtuple


SampleRequest = namedtuple('SampleRequest', 'sender')
DieRequest = namedtuple('DieRequest', 'sender')
ExchangeRequest = namedtuple('ExchangeRequest', 'sender partner exchanger params')

# CalculateProposalRequest = namedtuple('CalculateProposalRequest', 'sender receiver orig_replica')
