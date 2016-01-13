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
    # def gradient(self, *params):

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
        traj = GeneralTrajectory([traj.initial, traj.final], work=traj.work, heat=traj.heat)

        return traj
        
    
class LMDRENSProposer(AbstractRENSProposer):

    def _propagator_factory(self, pdf, params):

        from langevin import LangevinPropagator

        return LangevinPropagator(pdf.gradient, params.timestep, params.gamma)

    def propose(self, local_replica, partner_state, partner_energy, params):
        '''
        TODO: This is ugly
        '''
        
        traj = super(LMDRENSProposer, self).propose(local_replica, partner_state, partner_energy, params)
        for p in params.pdf_params:
            local_replica.pdf[p] = params.pdf_params[p][-1]
        E_remote = local_replica.get_energy(traj[0])
        for p in params.pdf_params:
            local_replica.pdf[p] = params.pdf_params[p][0]
        E_local = local_replica.get_energy(traj[-1])
        traj.work = (E_local - E_remote) - traj.heat

        return traj


class AMDRENSProposer(AbstractRENSProposer):

    def _propagator_factory(self, pdf, params):

        from csb.statistics.samplers.mc.propagators import ThermostattedMDPropagator

        return ThermostattedMDPropagator(pdf.gradient, params.timestep, params.collision_probability,
                                         params.update_interval)


from csb.statistics.samplers.mc.multichain import HMCStepRENS
import csb.statistics.samplers.mc.neqsteppropagator as noneqprops


class HMCStepRENSProposer(AbstractRENSProposer):

    def _setup_protocol(self, pdf, params):

        from collections import namedtuple
        from csb.numeric.integrators import FastLeapFrog
        from csb.statistics.samplers.mc.neqsteppropagator import Step, Protocol
        
        fields = 'timestep gradient hmc_traj_length hmc_iterations intermediate_steps mass_matrix integrator'
        FakeParams = namedtuple('FakeParams', fields)

        prot = lambda t, tau: t / tau
        t_prot = lambda t: prot(t, params.timestep * params.n_steps)
        fake_timestep = params.timestep
        n_steps = params.n_steps
        interp_pdf = InterpolatingPDF(pdf, params)
        im_log_probs = [lambda x, i=i: interp_pdf.log_prob(x, fake_timestep * i) 
                        for i in range(n_steps + 1)]
        im_reduced_hamiltonians = [noneqprops.ReducedHamiltonian(im_log_probs[i],
                                                                 temperature=1.0) 
                                   for i in range(n_steps + 1)]
        im_sys_infos = [noneqprops.HamiltonianSysInfo(im_reduced_hamiltonians[i])
                        for i in range(n_steps + 1)]
        perturbations = [noneqprops.ReducedHamiltonianPerturbation(im_sys_infos[i], im_sys_infos[i+1])
                        for i in range(n_steps)]

        fake_params = FakeParams(timestep=params.timestep, 
                                 gradient=interp_pdf.gradient,
                                 hmc_traj_length=1,
                                 hmc_iterations=1,
                                 intermediate_steps=params.n_steps,
                                 mass_matrix=None,
                                 integrator=FastLeapFrog)

        im_sys_infos = self._add_gradients(im_sys_infos, fake_params, t_prot)
        propagations = self._setup_propagations(im_sys_infos, fake_params)
        
        steps = [Step(perturbations[i], propagations[i]) for i in range(n_steps)]

        return Protocol(steps)

    def _setup_propagations(self, *params):

        return HMCStepRENS._setup_propagations(*params)

    def _add_gradients(self, *params):
        
        return HMCStepRENS._add_gradients(*params)
        
    def _propagator_factory(self, pdf, params):

        protocol = self._setup_protocol(pdf, params)

        return noneqprops.NonequilibriumStepPropagator(protocol)

    def propose(self, local_replica, partner_state, partner_energy, params):

        n_steps = params.n_steps
        propagator = self._propagator_factory(local_replica.pdf, params)

        from csb.statistics.samplers import State
        import numpy
        ps_pos = partner_state.position
        traj = propagator.generate(State(ps_pos, numpy.random.normal(size=ps_pos.shape)))
        traj = GeneralTrajectory([traj.initial, traj.final], work=traj.work)

        return traj        
