'''
Proposer classes which propose states for RE, RENS, ... swaps
'''

from rexfw.proposers import AbstractProposer, GeneralTrajectory


class REProposer(AbstractProposer):

    def propose(self, local_replica, partner_state, partner_energy, params):

        work =   local_replica.get_energy(partner_state) \
               - partner_energy

        return GeneralTrajectory([partner_state, partner_state], work=work)
