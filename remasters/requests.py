'''
Requests masters can send
'''

from collections import namedtuple


SampleRequest = namedtuple('SampleRequest', 'sender')
DieRequest = namedtuple('DieRequest', 'sender')
ProposeRequest = namedtuple('ProposeRequest', 'sender partner params')
AcceptBufferedProposalRequest = namedtuple('AcceptBufferedProposalRequest', 'sender accept')
GetStateAndEnergyRequest_master = namedtuple('GetStateAndEnergyRequest_master', 'sender partner')
SendGetStateAndEnergyRequest = namedtuple('SendGetStateAndEnergyRequest', 'sender partner')
DumpSamplesRequest = namedtuple('DumpSamplesRequest', 'sender samples_folder s_min, s_max, dump_step')
