'''
'''

import unittest


from rexfw import Parcel
from rexfw.remasters import ExchangeMaster
from rexfw.slgenerators import ExchangeParams
from rexfw.proposers.params import REProposerParams
from rexfw.test.cases.communicators import MockCommunicator
from rexfw.test.cases.statistics import MockStatistics, MockREStatistics
from rexfw.test.cases.slgenerators import MockSwapListGenerator
from rexfw.test.cases.proposers import MockProposer


class MockExchangeMaster(ExchangeMaster):

    def __init__(self, comm):

        replica_names = ['replica1', 'replica2', 'replica3']
        swap_params = [ExchangeParams(MockProposer(i, i+1), [REProposerParams()])
                       for i in range(len(replica_names) - 1)]

        super(MockExchangeMaster, self).__init__('remaster0',
                                                 replica_names,
                                                 swap_params,
                                                 MockStatistics(),
                                                 MockREStatistics(),
                                                 comm,
                                                 MockSwapListGenerator())
        

class testExchangeMaster(unittest.TestCase):

    def setUp(self):
        pass
    
    def _setUpExchangeMaster(self, comm):
    
        self._remaster = MockExchangeMaster(comm)
        self._replica_names = self._remaster.replica_names
        self._comm = self._remaster._comm
    
    def _checkParcel(self, last_sent, dest):

        self.assertTrue(isinstance(last_sent, Parcel))
        self.assertTrue(last_sent.sender == self._remaster.name)
        self.assertTrue(last_sent.receiver == dest)        

    def _checkProposeRequest(self, sent_obj, dest, partner):

        from rexfw.remasters.requests import ProposeRequest
        from rexfw.slgenerators import ExchangeParams

        self._checkParcel(sent_obj, dest)
        self.assertTrue(isinstance(sent_obj.data, ProposeRequest))
        request = sent_obj.data
        self.assertTrue(request.sender == self._remaster.name)
        self.assertTrue(request.partner == partner)
        self.assertTrue(isinstance(request.params, ExchangeParams))

    def testSendProposeRequest(self):
        
        from rexfw.slgenerators import ExchangeParams

        self._setUpExchangeMaster(MockCommunicator())

        self._remaster._send_propose_request(self._replica_names[0],
                                             self._replica_names[1],
                                             ExchangeParams([],[]))
        
        (last_sent, last_dest) = self._comm.sent[-1]
        self._checkProposeRequest(last_sent, self._replica_names[0],
                                  self._replica_names[1])
        
    def _checkGetStateAndEnergyRequest(self, sent_obj, dest, partner):

        from rexfw.remasters.requests import SendGetStateAndEnergyRequest
        
        self._checkParcel(sent_obj, dest)
        self.assertTrue(isinstance(sent_obj.data,
                                   SendGetStateAndEnergyRequest))
        request = sent_obj.data
        self.assertTrue(request.sender == self._remaster.name)
        self.assertTrue(request.partner == partner)
        
    def testSendGetStateAndEnergyRequest(self):

        self._setUpExchangeMaster(MockCommunicator())
        
        self._remaster._send_get_state_and_energy_request(self._replica_names[0],
                                                          self._replica_names[1])
        (last_sent, last_dest) = self._comm.sent[-1]
        self._checkGetStateAndEnergyRequest(last_sent,
                                            self._replica_names[1],
                                            self._replica_names[0])
        
        ## TODO: test whether communicator receives something?

    def testTriggerProposalCalculation(self):
        
        self._setUpExchangeMaster(MockCommunicator())
        
        for step in (0, 1):
            swap_list = self._remaster._calculate_swap_list(step)
            swap = swap_list[-1]
            r1 = swap[0]
            r2 = swap[1]
            params = swap[2]
            self._remaster._trigger_proposal_calculation(swap_list)
            params = swap[2]

            self._checkGetStateAndEnergyRequest(self._comm.sent[-4][0],
                                                    r2, r1)
            self._checkGetStateAndEnergyRequest(self._comm.sent[-3][0],
                                                    r1, r2)
            self._checkProposeRequest(self._comm.sent[-2][0],
                                      r1, r2)
            self._checkProposeRequest(self._comm.sent[-1][0],
                                      r2, r1)
            self.assertTrue(params.proposer_params.reverse_events == 2)           

    def testReceiveWorks(self):

        from rexfw.test.cases.communicators import WorkHeatSendingMockCommunicator
        
        self._setUpExchangeMaster(WorkHeatSendingMockCommunicator())
        
        for step in (0, 1):
            swap_list = self._remaster._calculate_swap_list(step)
            works, heats = self._remaster._receive_works(swap_list)

            self.assertTrue(len(works) == 1)
            self.assertTrue(len(heats) == 1)

            cwfs = self._remaster._comm.calculate_work_from_source
            chfs = self._remaster._comm.calculate_heat_from_source
            self.assertTrue(works[0][0] == cwfs(swap_list[0][0]))
            self.assertTrue(heats[0][0] == chfs(swap_list[0][0]))
            self.assertTrue(works[0][1] == cwfs(swap_list[0][1]))
            self.assertTrue(heats[0][1] == chfs(swap_list[0][1]))

    def testCalculateAcceptance(self):

        ## TODO
        pass

if __name__ == '__main__':

    unittest.main()
