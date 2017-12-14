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
    from rexfw.statistics import Statistics, REStatistics
    from rexfw.statistics.writers import StandardConsoleREStatisticsWriter, StandardFileMCMCStatisticsWriter, StandardFileREStatisticsWriter, StandardFileREWorksStatisticsWriter, StandardConsoleMCMCStatisticsWriter, StandardConsoleMCMCStatisticsWriter
    from rexfw.convenience import create_standard_RE_params
    from rexfw.convenience.statistics import create_standard_averages, create_standard_works, create_standard_stepsizes, create_standard_heats

    replica_names = ['replica{}'.format(i) for i in range(1, n_replicas + 1)]
    params = create_standard_RE_params(n_replicas)
        
    from rexfw.statistics.averages import REAcceptanceRateAverage, MCMCAcceptanceRateAverage
    from rexfw.statistics.logged_quantities import SamplerStepsize
    
    local_pacc_avgs = [MCMCAcceptanceRateAverage(r, 'x')
                       for r in replica_names]
    re_pacc_avgs = [REAcceptanceRateAverage(replica_names[i], replica_names[i+1]) 
                    for i in range(len(replica_names) - 1)]
    stepsizes = [SamplerStepsize(r, 'x') for r in replica_names]
    works = create_standard_works(replica_names)
    heats = create_standard_heats(replica_names)
    stats_path = sim_path + 'statistics/'
    stats_writers = [StandardConsoleMCMCStatisticsWriter(['x'],
                                                         ['acceptance rate',
                                                          'stepsize'
                                                          ]),
                     StandardFileMCMCStatisticsWriter(stats_path + '/mcmc_stats.txt',
                                                      ['x'],
                                                      ['acceptance rate',
                                                       'stepsize'])
                    ]
    stats = Statistics(elements=local_pacc_avgs + stepsizes, 
                       stats_writer=stats_writers)
    re_stats_writers = [StandardConsoleREStatisticsWriter(),
                        StandardFileREStatisticsWriter(stats_path + 're_stats.txt',
                                                       ['acceptance rate'])]
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
    import errno

    def make_sure_path_exists(path):
        try:
            os.makedirs(path)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise

    for sub in ('samples', 'statistics', 'works', 'heats', 'energies'):
        make_sure_path_exists(sim_folder + sub)
