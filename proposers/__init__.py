'''
Proposer classes which propose states for RE, RENS, ... swaps
'''

from abc import ABCMeta, abstractmethod

from rexfw import Parcel

class GeneralTrajectory(list):

    def __init__(self, items, work=0.0, heat=0.0):

        super(GeneralTrajectory, self).__init__(items)

        self.work = work
        self.heat = heat
        
        
class AbstractProposer(object):

    __metaclass__ = ABCMeta

    def __init__(self, name, comm):

        self.name = name
        self._comm = comm

    @abstractmethod
    def propose(self, local_replica, partner_state, partner_energy, params):
        pass


class REProposer(AbstractProposer):

    def propose(self, local_replica, partner_state, partner_energy, params):

        work =   local_replica.get_energy(partner_state) \
               - partner_energy

        return GeneralTrajectory([partner_state, partner_state], work=work)


class InterpolatingPDF(object):

    def __init__(self, pdf, params):

        self.pdf = pdf
        n_steps = params.n_steps
        dt = params.timestep
        pdf_params = params.pdf_params
        l = lambda t: t / (n_steps * dt)
        self.interp_params = lambda t: {name: (  1.0 - l(t)) * pdf_params[name][0] 
                                               + l(t) * pdf_params[name][1] 
                                               for name in pdf_params.iterkeys()}

    def log_prob(self, x, t):

        for name, value in self.interp_params(t).iteritems():
            self.pdf[name] = value

        return self.pdf.log_prob(x)

    def gradient(self, x, t):
        
        for name, value in self.interp_params(t).iteritems():
            self.pdf[name] = value

        return self.pdf.gradient(x)
        
    
class AbstractRENSProposer(AbstractProposer):

    def propose(self, local_replica, partner_state, partner_energy, params):

        n_steps = params.n_steps
        timestep = params.timestep
        pdf = InterpolatingPDF(local_replica.pdf, params)
        propagator = self._propagator_factory(pdf, params)

        from csb.statistics.samplers import State
        import numpy
        ps_pos = partner_state.position
        traj = propagator.generate(State(ps_pos, numpy.random.normal(size=ps_pos.shape)), n_steps)
        traj = GeneralTrajectory([traj.initial, traj.final], work=traj.work)

        return traj        
        
    
class LMDRENSProposer(AbstractRENSProposer):

    def _propagator_factory(self, pdf, params):

        from langevin import LangevinPropagator

        return LangevinPropagator(pdf.gradient, params.timestep, params.gamma)
