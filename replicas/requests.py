'''
Requests replicas can send
'''

from collections import namedtuple

        
GetStateAndEnergyRequest = namedtuple('GetStateAndEnergyRequest', 'sender')
StoreStateEnergyRequest = namedtuple('StoreStateEnergyRequest', 'sender state energy')
DoNothingRequest = namedtuple('DoNothingRequest', 'sender')
