'''
Proposer classes which propose states for RE, RENS, ... swaps
'''

from abc import ABCMeta, abstractmethod


class AbstractProposer(object):

    __metaclass__ = ABCMeta

    _request_processing_table = dict(
        CalculateProposalRequest='self.calculate_proposal({})',
        SendSetStateRequestRequest='self.send_set_state_request_request({})',
        )

    def process_request(self, request):

        dummy = None
        return eval(self._request_processing_table[request.__class__.__name__].format('request'))

    @abstractmethod
    def calculate_proposal(self, request):
        pass

    def send_set_state_request_request(self, request):
        
    

class REProposer(AbstractProposer):

    def calculate_proposal(self, request):

        target_replica = request.target_replica
        orig_replica = request.orig_replica

        proposal = self._comm.send_receive(GetStateRequest(), orig_replica)
        energy = self._postmaster.send_receive(GetEnergyRequest(proposal), target_replica)
        self._buffered_proposal = proposal
        self._buffered_request = requesting_replica_request
        return Parcel(request.dest, request.source, energy)
        
        
