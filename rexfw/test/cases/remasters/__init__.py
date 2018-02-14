'''
'''

import unittest
import numpy as np
from collections import deque

from rexfw import Parcel
from rexfw.remasters import ExchangeMaster
from rexfw.slgenerators import ExchangeParams
from rexfw.proposers.params import REProposerParams
from rexfw.test.cases.communicators import MockCommunicator
from rexfw.test.cases.communicators import DoNothingRequestReceivingMockCommunicator
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

class SwapsMockedExchangeMaster(MockExchangeMaster):

    def __init__(self):

        comm = DoNothingRequestReceivingMockCommunicator()
        super(SwapsMockedExchangeMaster, self).__init__(comm)

        self.callstack = deque()
        self.mockswaplist = lambda step: self._calculate_swap_list(step)
        self.mockworks = lambda n: np.zeros((n, 2))
        self.mockheats = self.mockworks
        self.mockaccs = lambda n: [True for _ in range(n)]

    def _trigger_proposal_calculation(self, swap_list):

        self.callstack.append(('trigger_proposal_calculation', (swap_list,)))

    def _receive_works(self, swap_list):

        self.callstack.append(('receive_works', (swap_list,)))

        return self.mockworks(len(swap_list)), self.mockheats(len(swap_list))

    def _calculate_acceptance(self, works):

        self.callstack.append(('calculate_acceptance', (works,)))

        return self.mockaccs(len(works))

    def _trigger_exchanges(self, swap_list, acc):

        self.callstack.append(('trigger_exchanges', (swap_list, acc)))
        super(SwapsMockedExchangeMaster, self)._trigger_exchanges(swap_list, acc)


class SendAcceptRejectMockedExchangeMaster(MockExchangeMaster):

    def __init__(self):

        comm = DoNothingRequestReceivingMockCommunicator()
        super(SendAcceptRejectMockedExchangeMaster, self).__init__(comm)

        self.callstack = deque()

    def _send_accept_exchange_request(self, dest):
        
        self.callstack.append(('send_accept_exchange_request', (dest, )))

    def _send_reject_exchange_request(self, dest):

        self.callstack.append(('send_reject_exchange_request', (dest, )))
        

class testExchangeMaster(unittest.TestCase):

    def setUp(self):
        pass
    
    def _setUpExchangeMaster(self, comm):
    
        self._remaster = MockExchangeMaster(comm)
        self._replica_names = self._remaster.replica_names
        self._comm = self._remaster._comm
    
    def _checkParcel(self, last_sent, dest, sender=None):

        if sender is None:
            sender = self._remaster.name
        self.assertTrue(isinstance(last_sent, Parcel))
        self.assertTrue(last_sent.sender == sender)
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

    def _checkAcceptBufferedProposalRequest(self, sent_obj, dest, acc):

        from rexfw.remasters.requests import AcceptBufferedProposalRequest

        self._checkParcel(sent_obj, dest)
        self.assertTrue(isinstance(sent_obj.data, AcceptBufferedProposalRequest))
        request = sent_obj.data
        self.assertTrue(request.sender == self._remaster.name)
        self.assertTrue(request.accept == acc)
        
    def _checkDoNothingRequest(self, received_obj, sender):

        from rexfw.replicas.requests import DoNothingRequest

        self._checkParcel(received_obj, dest=self._remaster.name, sender=sender)
        self.assertTrue(isinstance(received_obj.data, DoNothingRequest))
        request = received_obj.data
        self.assertTrue(request.sender == sender)

    def testSendProposeRequest(self):
        
        from rexfw.slgenerators import ExchangeParams

        self._setUpExchangeMaster(MockCommunicator())

        self._remaster._send_propose_request(self._replica_names[0],
                                             self._replica_names[1],
                                             ExchangeParams([],[]))
        
        (last_sent, last_dest) = self._comm.sent.pop()
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
        (last_sent, last_dest) = self._comm.sent.pop()
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

            self._checkGetStateAndEnergyRequest(self._comm.sent.popleft()[0],
                                                    r2, r1)
            self._checkGetStateAndEnergyRequest(self._comm.sent.popleft()[0],
                                                    r1, r2)
            self._checkProposeRequest(self._comm.sent.popleft()[0],
                                      r1, r2)
            self._checkProposeRequest(self._comm.sent.popleft()[0],
                                      r2, r1)
            self.assertTrue(params.proposer_params.reverse_events == 2)           

    def testReceiveWorks(self):

        from rexfw.test.cases.communicators import WorkHeatReceivingMockCommunicator
        
        self._setUpExchangeMaster(WorkHeatReceivingMockCommunicator())
        
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

    def testSendAcceptExchangeRequest(self):

        self._setUpExchangeMaster(MockCommunicator())

        for step in (0,1):
            swap_list = self._remaster._calculate_swap_list(step)
            for r1, r2, _ in swap_list:
                for r in (r1, r2):
                    self._remaster._send_accept_exchange_request(r)

                    sent_obj, _ = self._remaster._comm.sent.pop()
                    self._checkAcceptBufferedProposalRequest(sent_obj, r, True)

    def testSendRejectExchangeRequest(self):

        self._setUpExchangeMaster(MockCommunicator())

        for step in (0,1):
            swap_list = self._remaster._calculate_swap_list(step)
            for r1, r2, _ in swap_list:
                for r in (r1, r2):
                    self._remaster._send_reject_exchange_request(r)

                    sent_obj, _ = self._remaster._comm.sent[-1]
                    self._checkAcceptBufferedProposalRequest(sent_obj, r, False)

    def testTriggerExchanges(self):

        self._remaster = SendAcceptRejectMockedExchangeMaster()
        stack = self._remaster.callstack
        send_accept = 'send_accept_exchange_request'
        send_reject = 'send_reject_exchange_request'

        for step in (0, 1):
            swap_list = self._remaster._calculate_swap_list(step)
            n_swaps = len(swap_list)
            ## TODO: check all possible outcomes
            outcomes = [[True for _ in swap_list]]
            for acc in outcomes:
                self._remaster._trigger_exchanges(swap_list, acc)
             
                for i, (r1, r2, _) in enumerate(swap_list):
                    r1_request = stack.popleft()
                    r2_request = stack.popleft()
                    if acc[i]:
                        self.assertTrue(r1_request[0] == send_accept)
                        self.assertTrue(r2_request[0] == send_accept)
                    else:
                        self.assertTrue(r1_request[0] == send_reject)
                        self.assertTrue(r2_request[0] == send_reject)
                    self.assertTrue(len(r1_request[1]) == 1)
                    self.assertTrue(len(r2_request[1]) == 1)
                    self.assertTrue(r1_request[1][0] == r1)
                    self.assertTrue(r2_request[1][0] == r2)
                    rcvd_objs = self._remaster._comm.received
                    r1_rcvd = rcvd_objs.popleft()
                    r2_rcvd = rcvd_objs.popleft()
                    self._checkDoNothingRequest(r1_rcvd, r1)
                    self._checkDoNothingRequest(r2_rcvd, r2)

    def testPerformExchanges(self):

        self._remaster = SwapsMockedExchangeMaster()

        for step in (0, 1):
            swap_list = self._remaster._calculate_swap_list(step)
            n_swaps = len(swap_list)
            
            self._remaster._perform_exchanges(swap_list)
            stack = self._remaster.callstack

            tpc = stack.popleft()
            self.assertTrue(tpc[0] == 'trigger_proposal_calculation')
            self.assertTrue(len(tpc[1]) == 1)
            self.assertTrue(tpc[1][0] == swap_list)
            
            rw = stack.popleft()
            self.assertTrue(rw[0] == 'receive_works')
            self.assertTrue(len(rw[1]) == 1)
            self.assertTrue(rw[1][0] == swap_list)

            ca = stack.popleft()
            self.assertTrue(ca[0] == 'calculate_acceptance')
            self.assertTrue(len(ca[1]) == 1)
            self.assertTrue(np.all(ca[1][0] == self._remaster.mockworks(n_swaps)))
            
            te = stack.popleft()
            self.assertTrue(te[0] == 'trigger_exchanges')
            self.assertTrue(len(te[1]) == 2)
            self.assertTrue(te[1][0] == swap_list)
            self.assertTrue(np.all(te[1][1] == self._remaster.mockaccs(n_swaps)))

    def testGetNoExReplicas(self):

        self._setUpExchangeMaster(MockCommunicator())

        for step in (0, 1):
            swap_list = self._remaster._calculate_swap_list(step)
            no_exchange = self._remaster._get_no_ex_replicas(swap_list)
            
            self.assertTrue(len(no_exchange) == 1)
            self.assertTrue(no_exchange[0] == self._replica_names[2]
                            if step == 0 else self._replica_names[0])

    def _checkSendStatsRequest(self, obj, sender):

        from rexfw.remasters.requests import SendStatsRequest

        self.assertTrue(isinstance(obj, SendStatsRequest))
        self.assertTrue(obj.sender == sender)

    def testSendSendStatsRequests(self):

        self._setUpExchangeMaster(MockCommunicator())

        self._remaster._send_send_stats_requests(self._replica_names)

        sent_objs = self._remaster._comm.sent
        for r in self._replica_names:
            obj = sent_objs.popleft()[0]
            self._checkParcel(obj, r)
            self._checkSendStatsRequest(obj.data, self._remaster.name)

    def testReceiveAndUpdateStats(self):

        self._setUpExchangeMaster(MockCommunicator())

        self._remaster._receive_and_update_stats(self._replica_names)

        recvd_objs = self._remaster._comm.received
        for r in self._replica_names:
            obj, source = recvd_objs.popleft()
            self._checkParcel(obj, self._remaster.name, r)
            self.assertTrue(source == r)
            update = self._remaster.sampling_statistics.update_stack.popleft()
            self.assertTrue(update[0] is None)
            self.assertTrue(len(update[1]) == 1)
            self.assertTrue(update[1][0] == r)

    def testWriteStatistics(self):

        self._setUpExchangeMaster(MockCommunicator())

        self._remaster._write_statistics(123)

        write_stack = self._remaster.sampling_statistics.write_stack
        self.assertTrue(len(write_stack) == 1)
        self.assertTrue(write_stack.pop() == 123)
        
        write_stack = self._remaster.swap_statistics.write_stack
        self.assertTrue(len(write_stack) == 1)
        self.assertTrue(write_stack.pop() == 123)

    def _checkSendSampleRequest(self, obj, sender):

        from rexfw.remasters.requests import SampleRequest

        self.assertTrue(isinstance(obj, SampleRequest))
        self.assertTrue(obj.sender == sender)

    def testSendSampleRequests(self):

        self._setUpExchangeMaster(MockCommunicator())

        self._remaster._send_sample_requests(self._replica_names)

        sent_objs = self._remaster._comm.sent
        for r in self._replica_names:
            obj, _ = sent_objs.popleft()
            self._checkParcel(obj, r, self._remaster.name)
            self._checkSendSampleRequest(obj.data, self._remaster.name)

    def _checkSendDumpSamplesRequest(self, obj, sender, folder, smin, smax,
                                     offset, dump_step):

        from rexfw.remasters.requests import DumpSamplesRequest

        self.assertTrue(isinstance(obj, DumpSamplesRequest))
        self.assertTrue(obj.sender == sender)
        self.assertTrue(obj.samples_folder == folder)
        self.assertTrue(obj.s_min == smin)
        self.assertTrue(obj.s_max == smax)
        self.assertTrue(obj.offset == offset)
        self.assertTrue(obj.dump_step == dump_step)        

    def testSendDumpSamplesRequest(self):

        self._setUpExchangeMaster(MockCommunicator())

        folder = 'bla'
        smin, smax = 1, 2
        offset = 3
        dump_step = 4
        self._remaster._send_dump_samples_request(folder, smin, smax, offset,
                                                  dump_step)

        sent_objs = self._remaster._comm.sent
        for r in self._replica_names:
            obj, _ = sent_objs.popleft()
            self._checkParcel(obj, r, self._remaster.name)
            self._checkSendDumpSamplesRequest(obj.data, self._remaster.name,
                                              folder, smin, smax, offset,
                                              dump_step)

    def _checkDieRequest(self, obj, sender):

        from rexfw.remasters.requests import DieRequest

        self.assertTrue(isinstance(obj, DieRequest))
        self.assertTrue(obj.sender == sender)

    def testTerminateReplicas(self):

        self._setUpExchangeMaster(MockCommunicator())

        self._remaster.terminate_replicas()

        sent_objs = self._remaster._comm.sent

        for r in self._replica_names:
            obj, _ = sent_objs.popleft()
            self._checkParcel(obj, r, self._remaster.name)
            self._checkDieRequest(obj.data, self._remaster.name)

if __name__ == '__main__':

    unittest.main()
