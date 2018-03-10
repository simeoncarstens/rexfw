'''
'''
import unittest
import numpy as np
from collections import deque

from rexfw.proposers import AbstractProposer, GeneralTrajectory, REProposer
from rexfw.test.cases.communicators import MockCommunicator


class MockProposer(AbstractProposer):

    def __init__(self, start=0, end=1):

        super(MockProposer, self).__init__('mock_proposer')
        self.traj = GeneralTrajectory([start, end])

    def propose(self, local_replica, partner_state, partner_energy, params):

        return self.traj


class testREProposer(unittest.TestCase):

    def setUp(self):

        self._proposer = REProposer('testproposer')

    def testPropose(self):

        from rexfw.test.cases.replicas import CalculateProposalMockReplica

        replica = CalculateProposalMockReplica(MockCommunicator())
        result = self._proposer.propose(replica, 4.2, 8.9, None)

        self.assertTrue(isinstance(result, GeneralTrajectory))
        self.assertEqual(result[0], 4.2)
        self.assertEqual(result[-1], 4.2)
        self.assertEqual(result.work, 42 - 8.9)


if __name__ == '__main__':

    unittest.main()

        
