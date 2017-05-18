'''
Proposer classes which propose states for RE, RENS, ... swaps
'''

import numpy

from abc import ABCMeta, abstractmethod

from csb.statistics.samplers import State
import csb.statistics.samplers.mc.neqsteppropagator as noneqprops

from rexfw import Parcel


class GeneralTrajectory(list):

    def __init__(self, items, work=0.0, heat=0.0):

        super(GeneralTrajectory, self).__init__(items)

        self.work = work
        self.heat = heat
        
        
class AbstractProposer(object):

    __metaclass__ = ABCMeta

    def __init__(self, name):

        self.name = name

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


class AbstractRENSProposer(AbstractProposer):

    def __init__(self, name, interpolating_pdf=ParamInterpolationPDF):

        super(AbstractRENSProposer, self).__init__(name)

        self._interpolating_pdf = interpolating_pdf
        
    def _pdf_factory(self, local_replica, params):

        if self._interpolating_pdf.__name__ ==  'OldISDInterpolatingPDF':
            pdf = self._interpolating_pdf(local_replica.pdf, params, self.posterior)
        else:
            pdf = self._interpolating_pdf(local_replica.pdf, params)

        return pdf

    @abstractmethod
    def _calculate_work(self, local_replica, partner_energy, traj):

        pass

    def propose(self, local_replica, partner_state, partner_energy, params):

        pdf = self._pdf_factory(local_replica, params)
        propagator = self._propagator_factory(pdf, params)

        start_state = self._augment_state(partner_state)
        traj = propagator.generate(start_state, params.n_steps)
        traj.work = self._calculate_work(local_replica, partner_energy, traj)

        traj = GeneralTrajectory([traj.initial, traj.final], work=traj.work, heat=traj.heat)

        return traj

    @abstractmethod
    def _augment_state(self, state):
        pass

    
class AbstractMDRENSProposer(AbstractRENSProposer):

    def _augment_state(self, state):

        state.momentum = numpy.random.normal(size=state.position.shape)

        return state

    def _calculate_work(self, local_replica, partner_energy, traj):

        E_remote = partner_energy
        E_local = -local_replica.pdf.log_prob(traj.final.position)
        H_local = E_local + 0.5 * numpy.sum(traj.final.momentum ** 2)
        H_remote = E_remote + 0.5 * numpy.sum(traj.initial.momentum ** 2)
        
        return H_local - H_remote - traj.heat        


class AbstractMCRENSProposer(AbstractRENSProposer):

    def _augment_state(self, state):

        return state

    def _calculate_work(self, local_replica, partner_energy, traj):

        E_remote = partner_energy
        E_local = -local_replica.pdf.log_prob(traj.final.position)
        
        return E_local - E_remote - traj.heat        


class MicrocanonicalMDRENSProposer(AbstractMDRENSProposer):

    def _propagator_factory(self, pdf, params):

        from csb.statistics.samplers.mc.propagators import MDPropagator

        return MDPropagator(pdf.gradient, params.timestep)
    
    
class LMDRENSProposer(AbstractMDRENSProposer):

    def _propagator_factory(self, pdf, params):

        from langevin import LangevinPropagator

        return LangevinPropagator(pdf.gradient, params.timestep, gamma=params.gamma)


class AMDRENSProposer(AbstractMDRENSProposer):

    def _propagator_factory(self, pdf, params):

        from csb.statistics.samplers.mc.propagators import ThermostattedMDPropagator

        return ThermostattedMDPropagator(pdf.gradient, params.timestep, 
                                         collision_probability=params.collision_probability,
                                         update_interval=params.update_interval)


class AbstractStepRENSProposer(AbstractRENSProposer):

    def _setup_sys_infos(self, interp_pdf, n_steps):

        im_log_probs = [lambda x, i=i: interp_pdf.log_prob(x, i) 
                        for i in range(n_steps + 1)]

        im_reduced_hamiltonians = [noneqprops.ReducedHamiltonian(im_log_probs[i],
                                                                 temperature=1.0) 
                                   for i in range(n_steps + 1)]
        im_sys_infos = [noneqprops.HamiltonianSysInfo(im_reduced_hamiltonians[i])
                        for i in range(n_steps + 1)]

        return im_sys_infos

    def _setup_interp_pdf(self, n_steps, pdf_params):

        TempParams = namedtuple('TempParams', 'n_steps timestep pdf_params')
        p = TempParams(n_steps, 1.0, pdf_params)

        pdf = self._interpolating_pdf(pdf, p)

        return pdf
        
    def _setup_protocol(self, pdf, params):

        from collections import namedtuple
        from csb.statistics.samplers.mc.neqsteppropagator import Step, Protocol
        
        fields = 'timestep gradient hmc_traj_length hmc_iterations intermediate_steps mass_matrix integrator'
        FakeParams = namedtuple('FakeParams', fields)
        
        fake_timestep = params.timestep
        n_steps = params.n_steps


        interp_pdf = self._setup_interp_pdf(n_steps, params.pdf_params)
                
        im_sys_infos = self._setup_sys_infos(interp_pdf, n_steps)

        perturbations = [noneqprops.ReducedHamiltonianPerturbation(im_sys_infos[i], im_sys_infos[i+1])
                        for i in range(n_steps)]


        fake_params = FakeParams(timestep=params.timestep, 
                                 gradient=interp_pdf.gradient,
                                 hmc_traj_length=params.hmc_traj_length,
                                 hmc_iterations=params.n_hmc_iterations,
                                 intermediate_steps=params.n_steps,
                                 mass_matrix=None,
                                 integrator=FastLeapFrog)

        im_sys_infos = self._add_gradients(im_sys_infos, fake_params)
        propagations = self._setup_propagations(im_sys_infos, fake_params)
        steps = [Step(perturbations[i], propagations[i]) for i in range(n_steps)]
        
        return Protocol(steps)

    def _setup_propagations(self, *params):

        if True:
            from fastcode import FastHMCStepRENS

            return FastHMCStepRENS._setup_propagations(*params)
        else:
            ## leaks A LOT of memory, gotta fix this in CSB.
            from csb.statistics.samplers.mc.multichain import HMCStepRENS

            return HMCStepRENS._setup_propagations(*params)

    def _add_gradients(self, im_sys_infos, param_info):

        im_gradients = [lambda x, t, i=i: param_info.gradient(x, i)
                        for i in range(param_info.intermediate_steps + 1)]

        for i, s in enumerate(im_sys_infos):
            s.hamiltonian.gradient = im_gradients[i]

        return im_sys_infos
    
    def _propagator_factory(self, pdf, params):

        protocol = self._setup_protocol(pdf, params)
        
        return noneqprops.NonequilibriumStepPropagator(protocol)

    def propose(self, local_replica, partner_state, partner_energy, params):

        n_steps = params.n_steps
        propagator = self._propagator_factory(local_replica.pdf, params)

        ps_pos = partner_state.position
        traj = propagator.generate(State(ps_pos))
        traj = GeneralTrajectory([traj.initial, traj.final], work=traj.work)
        
        return traj        

    def _augment_state(self, state):
        pass

    def _calculate_work(self, local_replica, partner_energy, traj):
        pass


class HMCStepRENSProposer(AbstractRENSProposer):

    def _setup_protocol(self, pdf, params):

        from collections import namedtuple
        from csb.numeric.integrators import FastLeapFrog
        from csb.statistics.samplers.mc.neqsteppropagator import Step, Protocol
        
        fields = 'timestep gradient hmc_traj_length hmc_iterations intermediate_steps mass_matrix integrator'
        FakeParams = namedtuple('FakeParams', fields)
        
        fake_timestep = params.timestep
        n_steps = params.n_steps

        Bla = namedtuple('Bla', 'n_steps timestep pdf_params')
        p = Bla(n_steps, 1.0, params.pdf_params)
        
        if self._interpolating_pdf.__name__ ==  'OldISDInterpolatingPDF':
            pdf = self._interpolating_pdf(pdf, p, self.posterior)
            print "loaded proprietary posterior"
        else:
            pdf = self._interpolating_pdf(pdf, p)

        interp_pdf = pdf
                
        # class P(object):
        #     def log_prob(self, x, i):
        #         i=float(i)
        #         old = pdf['sigma']
        #         pdf['sigma'] = params.pdf_params['sigma'][0]
        #         a = pdf.log_prob(x)
        #         pdf['sigma'] = params.pdf_params['sigma'][-1]
        #         b = pdf.log_prob(x)
        #         pdf['sigma']=old

        #         return i / float(n_steps) * b + (1.0 - i / float(n_steps)) * a
            
        #     def gradient(self, x, i):

        #         l = i / float(n_steps)
                
        #         l=float(l)
        #         # print l
        #         old = pdf['sigma']
        #         pdf['sigma'] = params.pdf_params['sigma'][0]
        #         a = pdf.gradient(x)
        #         pdf['sigma'] = params.pdf_params['sigma'][-1]
        #         b = pdf.gradient(x)
        #         pdf['sigma']=old

        #         return l * b + (1.0 - l) * a
        
        im_log_probs = [lambda x, i=i: interp_pdf.log_prob(x, i) 
                        for i in range(n_steps + 1)]

        im_reduced_hamiltonians = [noneqprops.ReducedHamiltonian(im_log_probs[i],
                                                                 temperature=1.0) 
                                   for i in range(n_steps + 1)]
        im_sys_infos = [noneqprops.HamiltonianSysInfo(im_reduced_hamiltonians[i])
                        for i in range(n_steps + 1)]
        perturbations = [noneqprops.ReducedHamiltonianPerturbation(im_sys_infos[i], im_sys_infos[i+1])
                        for i in range(n_steps)]


        ## before I mixed up hmc_traj_length and hmc_iterations, check whether this was acutally a good idea
        fake_params = FakeParams(timestep=params.timestep, 
                                 gradient=interp_pdf.gradient,
                                 hmc_traj_length=params.hmc_traj_length,
                                 hmc_iterations=params.n_hmc_iterations,
                                 intermediate_steps=params.n_steps,
                                 mass_matrix=None,
                                 integrator=FastLeapFrog)

        im_sys_infos = self._add_gradients(im_sys_infos, fake_params)
        propagations = self._setup_propagations(im_sys_infos, fake_params)
        steps = [Step(perturbations[i], propagations[i]) for i in range(n_steps)]
        
        return Protocol(steps)

    def _setup_propagations(self, *params):

        if True:
            from fastcode import FastHMCStepRENS

            return FastHMCStepRENS._setup_propagations(*params)
        else:
            ## leaks A LOT of memory, gotta fix this in CSB.
            from csb.statistics.samplers.mc.multichain import HMCStepRENS

            return HMCStepRENS._setup_propagations(*params)

    def _add_gradients(self, im_sys_infos, param_info):

        im_gradients = [lambda x, t, i=i: param_info.gradient(x, i)
                        for i in range(param_info.intermediate_steps + 1)]

        for i, s in enumerate(im_sys_infos):
            s.hamiltonian.gradient = im_gradients[i]

        return im_sys_infos
    
    def _propagator_factory(self, pdf, params):

        protocol = self._setup_protocol(pdf, params)
        
        return noneqprops.NonequilibriumStepPropagator(protocol)

    def propose(self, local_replica, partner_state, partner_energy, params):

        n_steps = params.n_steps
        propagator = self._propagator_factory(local_replica.pdf, params)

        ps_pos = partner_state.position
        traj = propagator.generate(State(ps_pos))
        traj = GeneralTrajectory([traj.initial, traj.final], work=traj.work)
        
        return traj        
