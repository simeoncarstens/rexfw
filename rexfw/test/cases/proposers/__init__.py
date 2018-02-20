'''
'''

from rexfw.proposers import AbstractProposer, GeneralTrajectory


class MockProposer(AbstractProposer):

    def __init__(self, start=0, end=1):

        super(MockProposer, self).__init__('mock_proposer')
        self.traj = GeneralTrajectory([start, end])

    def propose(self, local_replica, partner_state, partner_energy, params):

        return self.traj
