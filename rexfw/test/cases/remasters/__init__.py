'''
'''

import unittest


from rexfw import Parcel
from rexfw.remasters import ExchangeMaster
from rexfw.remasters.requests import ProposeRequest
from rexfw.slgenerators import ExchangeParams
from rexfw.proposers.params import REProposerParams
from rexfw.test.cases.communicators import MockCommunicator
from rexfw.test.cases.statistics import MockStatistics, MockREStatistics
from rexfw.test.cases.slgenerators import MockSwapListGenerator
from rexfw.test.cases.proposers import MockProposer


class MockExchangeMaster(ExchangeMaster):

    def __init__(self):

        replica_names = ['replica1', 'replica2', 'replica3']
        swap_params = [ExchangeParams(MockProposer(i, i+1), [REProposerParams()])
                       for i in range(len(replica_names) - 1)]

        super(MockExchangeMaster, self).__init__('remaster0',
                                                 replica_names,
                                                 swap_params,
                                                 MockStatistics(),
                                                 MockREStatistics(),
                                                 MockCommunicator(),
                                                 MockSwapListGenerator())
        

class testExchangeMaster(unittest.TestCase):

    def setUp(self):

        self._remaster = MockExchangeMaster()
        self._replica_names = self._remaster.replica_names
        self._comm = self._remaster._comm

    def checkParcel(self, last_sent, dest):

        self.assertTrue(isinstance(last_sent, Parcel))
        self.assertTrue(last_sent.sender == self._remaster.name)
        self.assertTrue(last_sent.receiver == dest)        

    def testSendProposeRequest(self):

        self._remaster._send_propose_request(self._replica_names[0],
                                             self._replica_names[1],
                                             'propose request')
        
        last_sent = self._comm.last_sent
        self.checkParcel(last_sent, self._replica_names[0])
        self.assertTrue(isinstance(last_sent.data, ProposeRequest))
        request = last_sent.data
        self.assertTrue(request.sender == self._remaster.name)
        self.assertTrue(request.partner == self._replica_names[1])
        self.assertTrue(request.params == 'propose request')

    def testSendGetStateAndEnergyRequest(self):

        from rexfw.remasters.requests import SendGetStateAndEnergyRequest

        self._remaster._send_get_state_and_energy_request(self._replica_names[0],
                                                          self._replica_names[1])
        last_sent = self._comm.last_sent
        last_received = self._comm.last_received


        self.checkParcel(last_sent, self._replica_names[1])
        self.assertTrue(isinstance(last_sent.data,
                                   SendGetStateAndEnergyRequest))
        request = last_sent.data
        self.assertTrue(request.sender == self._remaster.name)
        self.assertTrue(request.partner == self._replica_names[0])

        
if __name__ == '__main__':

    unittest.main()
