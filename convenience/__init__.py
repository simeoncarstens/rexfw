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


def setup_default_re_master(n_replicas, sim_path, comm):

    from rexfw.remasters import ExchangeMaster
    from rexfw.statistics import MCMCSamplingStatistics, REStatistics
    from rexfw.statistics.writers import StandardConsoleREStatisticsWriter, StandardFileMCMCStatisticsWriter, StandardFileREStatisticsWriter, StandardFileREWorksStatisticsWriter, StandardConsoleMCMCStatisticsWriter
    from rexfw.convenience.statistics import create_standard_averages, create_standard_works, create_standard_stepsizes, create_standard_heats

    replica_names = ['replica{}'.format(i) for i in range(1, n_replicas + 1)]
    params = create_standard_RE_params(n_replicas)
        
    local_pacc_avgs, re_pacc_avgs = create_standard_averages(replica_names)
    stepsizes = create_standard_stepsizes(replica_names)
    works = create_standard_works(replica_names)
    heats = create_standard_heats(replica_names)
    stats_path = sim_path + 'statistics/'
    stats_writers = [StandardConsoleMCMCStatisticsWriter(),
                     StandardFileMCMCStatisticsWriter(stats_path + '/mcmc_stats.txt')]
    stats = MCMCSamplingStatistics(comm, elements=local_pacc_avgs + stepsizes, 
                                   stats_writer=stats_writers)
    re_stats_writers = [StandardConsoleREStatisticsWriter(),
                        StandardFileREStatisticsWriter(stats_path + 're_stats.txt')]
    works_path = sim_path + 'works/'
    works_writers = [StandardFileREWorksStatisticsWriter(works_path)]
    re_stats = REStatistics(elements=re_pacc_avgs,
                            work_elements=works, heat_elements=heats,
                            stats_writer=re_stats_writers,
                            works_writer=works_writers)
    
    master = ExchangeMaster('master0', replica_names, params, comm=comm, 
                            sampling_statistics=stats, swap_statistics=re_stats)

    return master

def create_directories(sim_folder):

    import os

    os.system('mkdir '+sim_folder)
    samplespath = sim_folder + 'samples/'
    os.system('mkdir '+samplespath)
    statspath = sim_folder + 'statistics/'
    os.system('mkdir '+statspath)
    workspath = sim_folder + 'works/'
    os.system('mkdir '+workspath)
    heatspath = sim_folder + 'heats/'
    os.system('mkdir '+heatspath)
    energiespath = sim_folder + 'energies/'
    os.system('mkdir '+energiespath)
