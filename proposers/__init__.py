'''
Proposer classes which propose states for RE, RENS, ... swaps
'''

import numpy

from abc import ABCMeta, abstractmethod

from csb.statistics.samplers import State

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


class ParamInterpolationPDF(object):

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

        old_values = {}
        for name, value in self.interp_params(t).iteritems():
            old_values.update(**{name: self.pdf[name]})
            self.pdf[name] = value

        res = self.pdf.log_prob(x)

        for name, value in old_values.iteritems():
            self.pdf[name] = value
            
        return res

    def gradient(self, x, t):

        old_values = {}
        for name, value in self.interp_params(t).iteritems():
            old_values.update(**{name: self.pdf[name]})
            self.pdf[name] = value

        res = self.pdf.gradient(x)

        for name, value in old_values.iteritems():
            self.pdf[name] = value
            
        return res


class OldISDInterpolatingPDF(object):
    '''
    Linear interpolation between two pdfs, p(x,t) = (1-l)*p(x; params0) + l*p(x; params1)
    '''
    
    def __init__(self, pdf, params):

        self.pdf = pdf
        n_steps = params.n_steps
        dt = params.timestep
        pdf_params = params.pdf_params
        self.l = lambda t: t / (n_steps * dt)
        from protlib import LambdaISDWrapper
        self._lambdaisdwrapper = LambdaISDWrapper((pdf_params['lammda'][0], pdf_params['q'][0]),
                                                  (pdf_params['lammda'][-1], pdf_params['q'][-1]),
                                                  self.pdf._isdwrapper.posterior)

    def log_prob(self, x, t):

        return self._lambdaisdwrapper.log_prob(x, self.l(t))
    
    def gradient(self, x, t):

        return self._lambdaisdwrapper.gradient(x, self.l(t))    


# if __name__ == '__main__':
#     import os
#     os.chdir('/baycells/home/carstens/projects/rens/py/sampling/')
#     from pdfs import UBQISDPosterior
#     pdf = UBQISDPosterior()
#     from collections import namedtuple
#     new = OldISDInterpolatingPDF(pdf, namedtuple('bla', 'n_steps timestep pdf_params')(100, 1.0, {'lammda': [1.0, 0.9], 'q': [1.0, 1.03]}))
#     x = numpy.random.normal(size=370, scale=7)
#     from protlib import LambdaISDWrapper
#     old = LambdaISDWrapper((1.0, 1.0), (0.9, 1.03), pdf._isdwrapper.posterior)

#     print old.log_prob(x, 1.0), new.log_prob(x, 1.0)
    
    
class AbstractRENSProposer(AbstractProposer):

    def __init__(self, name, comm, interpolating_pdf=ParamInterpolationPDF):

        super(AbstractRENSProposer, self).__init__(name, comm)

        self._interpolating_pdf = interpolating_pdf
        
    def propose(self, local_replica, partner_state, partner_energy, params):
        
        n_steps = params.n_steps
        timestep = params.timestep
        pdf = self._interpolating_pdf(local_replica.pdf, params)
        propagator = self._propagator_factory(pdf, params)
        
        ps_pos = partner_state.position
        traj = propagator.generate(State(ps_pos, numpy.random.normal(size=ps_pos.shape)), n_steps)
        
        E_remote = partner_energy
        E_local = -local_replica.pdf.log_prob(traj.final.position)
        
        traj.work = (E_local - E_remote) + 0.5 * numpy.sum(traj.final.momentum ** 2) - 0.5 * numpy.sum(traj.initial.momentum ** 2) - traj.heat
        
        traj = GeneralTrajectory([traj.initial, traj.final], work=traj.work, heat=traj.heat)

        return traj

    
class MDRENSProposer(AbstractRENSProposer):

    def _propagator_factory(self, pdf, params):

        from csb.statistics.samplers.mc.propagators import MDPropagator

        return MDPropagator(pdf.gradient, params.timestep)
    
    
class LMDRENSProposer(AbstractRENSProposer):

    def _propagator_factory(self, pdf, params):

        from langevin import LangevinPropagator

        return LangevinPropagator(pdf.gradient, params.timestep, params.gamma)


class AMDRENSProposer(AbstractRENSProposer):

    def _propagator_factory(self, pdf, params):

        from csb.statistics.samplers.mc.propagators import ThermostattedMDPropagator

        return ThermostattedMDPropagator(pdf.gradient, params.timestep, 
                                         collision_probability=params.collision_probability,
                                         update_interval=params.update_interval)


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
        fake_timestep = params.timestep
        n_steps = params.n_steps
        t_prot = lambda t: prot(t, n_steps)

        Bla = namedtuple('Bla', 'n_steps timestep pdf_params')
        p = Bla(n_steps, 1.0, params.pdf_params)
        
        interp_pdf = self._interpolating_pdf(pdf, p)
        
        im_log_probs = [lambda x, i=i: interp_pdf.log_prob(x, i) 
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

        im_sys_infos = self._add_gradients(im_sys_infos, fake_params, t_prot)#, grads)
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

        ps_pos = partner_state.position
        traj = propagator.generate(State(ps_pos, numpy.random.normal(size=ps_pos.shape)))
        traj = GeneralTrajectory([traj.initial, traj.final], work=traj.work)

        return traj        
