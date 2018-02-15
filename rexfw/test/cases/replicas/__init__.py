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

        super(MockReplica, self).__init__('asdf', 4, MockPDF(), {'testparam': 5},
                                          MockSampler, {'testparam': 4}, MockProposer(),
                                          comm)

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
        pass
        #self._replica.initialize()
        


if __name__ == '__main__':

    unittest.main()

