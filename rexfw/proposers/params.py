'''
Simple parameter objects holding information :class:`.AbstractProposer` objects
might need to calculate proposals
'''

from abc import abstractmethod


class AbstractProposerParams(object):
    
    @abstractmethod
    def reverse(self):
        '''
        Reverses certain parameters to reuse this object for both
        forward and reverse trajectories
        '''
        pass


class REProposerParams(AbstractProposerParams):

    def reverse(self):
        pass


class AbstractRENSProposerParams(AbstractProposerParams):

    def __init__(self, pdf_params):

        self.pdf_params = pdf_params

    def reverse(self):

        for param_name in self.pdf_params:
            self.pdf_params[param_name] = self.pdf_params[param_name][::-1]


class LMDRENSProposerParams(AbstractRENSProposerParams):

    def __init__(self, pdf_params, n_steps, timestep, gamma):

        super(LMDRENSProposerParams, self).__init__(pdf_params)

        self.n_steps = n_steps
        self.timestep = timestep
        self.gamma = gamma


class AMDRENSProposerParams(AbstractRENSProposerParams):

    def __init__(self, pdf_params, n_steps, timestep, collision_probability=0.1, update_interval=1):

        super(AMDRENSProposerParams, self).__init__(pdf_params)

        self.n_steps = n_steps
        self.timestep = timestep
        self.collision_probability = collision_probability
        self.update_interval = update_interval


class HMCStepRENSProposerParams(AbstractRENSProposerParams):

    def __init__(self, pdf_params, n_steps, timestep, hmc_traj_length, n_hmc_iterations):

        super(HMCStepRENSProposerParams, self).__init__(pdf_params)

        self.n_steps = n_steps
        self.timestep = timestep
        self.n_hmc_iterations = n_hmc_iterations
        self.hmc_traj_length = hmc_traj_length
