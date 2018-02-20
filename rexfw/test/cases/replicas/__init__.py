'''
'''

import unittest
import numpy as np
from collections import deque

from rexfw import Parcel
from rexfw.remasters import ExchangeMaster
from rexfw.slgenerators import ExchangeParams
from rexfw.proposers.params import REProposerParams
from rexfw.replicas import Replica
from rexfw.test.cases.communicators import MockCommunicator
from rexfw.test.cases.communicators import DoNothingRequestReceivingMockCommunicator
from rexfw.test.cases.statistics import MockStatistics, MockREStatistics
from rexfw.test.cases.slgenerators import MockSwapListGenerator
from rexfw.test.cases.proposers import MockProposer

class MockPDF(object):

    def log_prob(self, x):

        return x

class MockReplica(Replica):

    def __init__(self, comm):

        super(MockReplica, self).__init__('replica1', 4, MockPDF(), {'testparam': 5},
                                          MockSampler, {'testparam': 4}, 
                                          {'mock_proposer1': MockProposer()},
                                          comm)

        self._request_processing_table.update(TestRequest='self._process_test_request({})')
        self.test_request_processed = 0

    def _process_test_request(self, request):

        self.test_request_processed += 1

        
class ProposeMockReplica(MockReplica):

    def __init__(self, comm):

        super(ProposeMockReplica, self).__init__(comm)

        self.works_heats_sent = False
        self._buffered_partner_state = 34
        self._buffered_partner_energy = 66

    def _calculate_proposal(self, request):

        from rexfw.proposers import GeneralTrajectory
        
        return GeneralTrajectory([0, 4], 23, 42)

    def _send_works_heats(self, proposal):

        self.works_heats_sent = True
    

class SetupSamplerMockReplica(Replica):

    def __init__(self):

        self.sampler_class = MockSampler
        self.pdf = MockPDF()
        self._state = 5
        self.sampler_params = {'testparam': 4}


class MockSampler(object):

    def __init__(self, pdf, state, testparam):

        self.pdf = pdf
        self.state = state
        self.testparam = testparam
        self.last_sampled = None
        self.sampler_stats = None

    def sample(self):

        self.last_sampled = self.state ** 2
        
        return self.last_sampled

    def get_last_draw_stats(self):

        return 'nope'


class testReplica(unittest.TestCase):

    def setUp(self):

        self._replica = MockReplica(MockCommunicator())

    def testSetupSampler(self):

        self._replica = SetupSamplerMockReplica()
        
        self._replica._setup_sampler()

        self.assertTrue(isinstance(self._replica._sampler, MockSampler))
        sampler = self._replica._sampler
        self.assertTrue(isinstance(sampler.pdf, MockPDF))
        self.assertTrue(sampler.state == self._replica.state)
        self.assertTrue(sampler.testparam == 4)

    def testStateGetter(self):
        ## TODO
        pass

    def testStateSetter(self):
        ## TODO
        pass

    def _checkParcel(self, obj, dest, sender=None):
        ## TODO: code duplication; similar code in other test cases
        from rexfw import Parcel

        if sender is None:
            sender = self._replica.name
        self.assertTrue(isinstance(obj, Parcel))
        self.assertTrue(obj.sender == sender)
        self.assertTrue(obj.receiver == dest)
    
    def testSendStateAndEnergy(self):

        from rexfw.replicas.requests import GetStateAndEnergyRequest
        
        sender = self._replica.name
        other = 'replica23'
        req = GetStateAndEnergyRequest(other)
        self._replica._send_state_and_energy(req)

        last_sent, dest = self._replica._comm.sent.pop()
        self.assertTrue(dest == other)
        self._checkParcel(last_sent, other, sender)
        self.assertTrue(last_sent.data.sender == self._replica.name)
        self.assertTrue(last_sent.data.state == self._replica.state)
        self.assertTrue(last_sent.data.energy == self._replica.energy)

    def testSendGetStateAndEnergyRequest(self):

        from rexfw.remasters.requests import SendGetStateAndEnergyRequest
        from rexfw.replicas.requests import GetStateAndEnergyRequest
        
        other = 'replica123'
        req = SendGetStateAndEnergyRequest('remaster0', other)
        self._replica._send_get_state_and_energy_request(req)

        last_sent, dest = self._replica._comm.sent.pop()
        self.assertTrue(dest == 'replica123')
        self._checkParcel(last_sent, other, self._replica.name)
        self.assertTrue(isinstance(last_sent.data, GetStateAndEnergyRequest))
        self.assertTrue(last_sent.data.sender == self._replica.name)

    def testStoreStateEnergy(self):

        from rexfw.replicas.requests import StoreStateEnergyRequest, DoNothingRequest

        other = 'replica234'
        req = StoreStateEnergyRequest(other, 2.5, 99)
        self._replica._store_state_energy(req)

        self.assertTrue(self._replica._buffered_partner_state == 2.5)
        self.assertTrue(self._replica._buffered_partner_energy == 99)
        last_sent, dest = self._replica._comm.sent.pop()
        self.assertTrue(dest == self._replica._current_master)
        self._checkParcel(last_sent, self._replica._current_master, self._replica.name)
        self.assertTrue(isinstance(last_sent.data, DoNothingRequest))
        self.assertTrue(last_sent.data.sender == self._replica.name)

    def testSample(self):

        old_state = self._replica.state
        self._replica._sample(None)
        
        self.assertTrue(self._replica._sampler.last_sampled == old_state ** 2)
        self.assertTrue(self._replica.samples[-1] == old_state ** 2)
        self.assertTrue(self._replica.sampler_stats[-1][0] == 0)
        self.assertTrue(self._replica.sampler_stats[-1][1] == 'nope')
        self.assertTrue(self._replica.ctr == 1)
        self.assertTrue(self._replica.energy_trace[-1] == -old_state ** 2)

    def testSendStats(self):

        from rexfw.remasters.requests import SendStatsRequest
        
        self._replica.sampler_stats.append(123)
        self._replica._send_stats(SendStatsRequest('remaster23'))
        
        last_sent, dest = self._replica._comm.sent.pop()
        self.assertTrue(dest == 'remaster23')
        self._checkParcel(last_sent, 'remaster23', self._replica.name)
        self.assertTrue(isinstance(last_sent.data, list))
        self.assertTrue(last_sent.data[-1] == 123)

    def _makeTmpDirs(self):

        import os
        from tempfile import mkdtemp
        
        tmpdir = mkdtemp()
        tmp_sample_folder = '{}/samples/'.format(tmpdir)
        os.makedirs(tmp_sample_folder)
        os.makedirs('{}/energies/'.format(tmpdir))        

        return tmpdir
        
    def testDumpSamples(self):

        import os
        import numpy as np
        from rexfw.remasters.requests import DumpSamplesRequest

        tmpdir = self._makeTmpDirs()
        tmp_samples_folder = '{}/samples/'.format(tmpdir)
        smin, smax = 3000, 4000
        offset = 2
        step = 2
        req = DumpSamplesRequest('remaster45', tmp_samples_folder, smin, smax, offset, step)
        buffered_samples = np.arange(1000)
        self._replica.samples = buffered_samples
        self._replica._dump_samples(req)

        fname = '{}/samples_{}_{}-{}.pickle'.format(tmp_samples_folder,
                                                    self._replica.name,
                                                    smin + offset,
                                                    smax + offset)
        self.assertTrue(os.path.exists(fname))
        dumped_samples = np.load(fname)
        self.assertTrue(np.all(np.array(dumped_samples) == buffered_samples[::step]))
        self.assertTrue(len(self._replica.samples) == 0)

    def testDumpEnergies(self):

        import os
        import numpy as np
        from rexfw.remasters.requests import DumpSamplesRequest

        tmpdir = self._makeTmpDirs()
        tmp_samples_folder = '{}/samples/'.format(tmpdir)
        tmp_energies_folder = '{}/energies/'.format(tmpdir)
        req = DumpSamplesRequest('remaster45', tmp_samples_folder, None, None, None, None)
        self._replica.energy_trace = [3]
        self._replica._dump_energies(req)

        fname = '{}{}.npy'.format(tmp_energies_folder, self._replica.name)
        self.assertTrue(os.path.exists(fname))
        energies = np.load(fname)
        self.assertTrue(len(energies) == 1)
        self.assertTrue(energies[0] == 3)
        self.assertTrue(len(self._replica.energy_trace) == 0)

    def testProcessRequest(self):

        from collections import namedtuple

        TestRequest = namedtuple('TestRequest', '')
        self._replica.process_request(TestRequest())

        self.assertTrue(self._replica.test_request_processed == 1)

    def testPropose(self):

        from rexfw.remasters import ProposeRequest
        from rexfw.slgenerators import ExchangeParams
        from rexfw.proposers.params import REProposerParams
        
        self._replica = ProposeMockReplica(MockCommunicator())

        req = ProposeRequest('remaster34', 'replica22', 
                             ExchangeParams(['mock_proposer1', 'mock_proposer2'],
                                            REProposerParams()))
        self._replica._propose(req)

        self.assertTrue(self._replica.works_heats_sent)
        self.assertTrue(self._replica._buffered_proposal == 4)
        
if __name__ == '__main__':

    unittest.main()

