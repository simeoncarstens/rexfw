'''
Convenience stuff to simplify standard tasks with this framework
'''


def create_standard_RE_params(n_replicas):

    from rexfw.slgenerators import ExchangeParams
    from rexfw.proposers.params import REProposerParams

    param_list = [ExchangeParams(['prop{}'.format(i), 'prop{}'.format(i+1)], REProposerParams()) 
                  for i in range(1, n_replicas)]

    return param_list

def create_standard_HMCStepRENS_params(schedule, n_intermediate_steps, hmc_traj_length, 
                                       n_hmc_iterations, timesteps):

    from rexfw.slgenerators import ExchangeParams
    from rexfw.proposers.params import HMCStepRENSProposerParams

    prop_params = [HMCStepRENSProposerParams(pdf_params={k: (schedule[k][i+1], schedule[k][i]) 
                                                         for k in schedule.keys()}, 
                                              n_steps=n_intermediate_steps,
                                              timestep=timesteps[i],
                                              hmc_traj_length=hmc_traj_length,
                                              n_hmc_iterations=n_hmc_iterations)
                   for i in range(len(timesteps))]
    param_list = [ExchangeParams(['prop{}'.format(i+1), 'prop{}'.format(i+2)], prop_params[i]) 
                  for i in range(len(prop_params))]

    return param_list

def create_standard_LMDRENS_params(schedule, n_steps, timesteps, gamma):

    from rexfw.slgenerators import ExchangeParams
    from rexfw.proposers.params import LMDRENSProposerParams

    prop_params = [LMDRENSProposerParams({k: (schedule[k][i+1], schedule[k][i]) 
                                              for k in schedule.keys()}, 
                                              n_steps, timesteps[i], gamma)
                   for i in range(len(timesteps))]
    param_list = [ExchangeParams(['prop{}'.format(i+1), 'prop{}'.format(i+2)], prop_params[i]) 
                  for i in range(len(prop_params))]

    return param_list
    

def create_standard_LMDRENS_params(schedule, n_steps, timesteps, gamma):

    from rexfw.slgenerators import ExchangeParams
    from rexfw.proposers.params import LMDRENSProposerParams

    prop_params = [LMDRENSProposerParams({k: (schedule[k][i+1], schedule[k][i]) 
                                              for k in schedule.keys()}, 
                                              n_steps, timesteps[i], gamma)
                   for i in range(len(timesteps))]
    param_list = [ExchangeParams(['prop{}'.format(i+1), 'prop{}'.format(i+2)], prop_params[i]) 
                  for i in range(len(prop_params))]

    return param_list


def create_standard_AMDRENS_params(schedule, n_steps, timesteps, 
                                   collision_probability=0.1, update_interval=1):

    from rexfw.slgenerators import ExchangeParams
    from rexfw.proposers.params import AMDRENSProposerParams

    prop_params = [AMDRENSProposerParams({k: (schedule[k][i+1], schedule[k][i]) 
                                              for k in schedule.keys()}, 
                                              n_steps, timesteps[i], 
                                              collision_probability, update_interval)
                   for i in range(len(timesteps))]
    param_list = [ExchangeParams(['prop{}'.format(i+1), 'prop{}'.format(i+2)], prop_params[i]) 
                  for i in range(len(prop_params))]

    return param_list