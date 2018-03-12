'''
Requests replicas can send to :class:`.ExchangeMaster` or other :class:`.Replica` objects
'''

from collections import namedtuple

        
GetStateAndEnergyRequest = namedtuple('GetStateAndEnergyRequest', 'sender')
StoreStateEnergyRequest = namedtuple('StoreStateEnergyRequest', 'sender state energy')
DoNothingRequest = namedtuple('DoNothingRequest', 'sender')
