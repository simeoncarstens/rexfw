'''
Convenient functions creating default objects to simplify standard tasks with this framework
'''


def create_default_RE_params(n_replicas):
    '''
    Creates default RE exchange parameters

    :param int n_replicas: the number of replicas

    :return: a list of parameter objects holding information required to perform swaps
    :rtype: list of :class:`.ExchangeParams`
    '''

    from rexfw.slgenerators import ExchangeParams
    from rexfw.proposers.params import REProposerParams

    param_list = [ExchangeParams(['prop{}'.format(i), 'prop{}'.format(i+1)], REProposerParams()) 
                  for i in range(1, n_replicas)]

    return param_list

def create_default_HMCStepRENS_params(schedule, n_intermediate_steps, hmc_traj_length, 
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

def create_default_LMDRENS_params(schedule, n_steps, timesteps, gamma):

    from rexfw.slgenerators import ExchangeParams
    from rexfw.proposers.params import LMDRENSProposerParams

    prop_params = [LMDRENSProposerParams({k: (schedule[k][i+1], schedule[k][i]) 
                                              for k in schedule.keys()}, 
                                              n_steps, timesteps[i], gamma)
                   for i in range(len(timesteps))]
    param_list = [ExchangeParams(['prop{}'.format(i+1), 'prop{}'.format(i+2)], prop_params[i]) 
                  for i in range(len(prop_params))]

    return param_list
    

def create_default_LMDRENS_params(schedule, n_steps, timesteps, gamma):

    from rexfw.slgenerators import ExchangeParams
    from rexfw.proposers.params import LMDRENSProposerParams

    prop_params = [LMDRENSProposerParams({k: (schedule[k][i+1], schedule[k][i]) 
                                              for k in schedule.keys()}, 
                                              n_steps, timesteps[i], gamma)
                   for i in range(len(timesteps))]
    param_list = [ExchangeParams(['prop{}'.format(i+1), 'prop{}'.format(i+2)], prop_params[i]) 
                  for i in range(len(prop_params))]

    return param_list


def create_default_AMDRENS_params(schedule, n_steps, timesteps, 
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



def create_default_stats_elements(replica_names, variable_name):
    '''
    Creates default sampling statistics "elements", each representing
    a tracked quantity such as acceptance rate, step size etc.

    :param replica_names: a list of all replica names
    :type replica_names: list

    :return: MCMC acceptance rate, RE acceptance rate and step size quantity objects
    :rtype: tuple
    '''

    from rexfw.convenience.statistics import create_default_MCMC_averages
    from rexfw.convenience.statistics import create_default_RE_averages
    from rexfw.convenience.statistics import create_default_stepsizes    

    mcmc_pacc_avgs = create_default_MCMC_averages(replica_names, variable_name)
    re_pacc_avgs = create_default_RE_averages(replica_names)
    stepsizes = create_default_stepsizes(replica_names, variable_name)
    
    return mcmc_pacc_avgs, re_pacc_avgs, stepsizes    

def create_default_stats_writers(sim_path, variable_name):
    '''
    Creates default statistics writers, which print sampling statistics
    on the screen or write it to a text file

    :param str sim_path: the output folder
    :param str variable_name: the name of the only variable to be sampled

    :return: default MCMC and RE statistics writers
    :rtype: tuple
    '''
    
    from rexfw.statistics.writers import StandardConsoleREStatisticsWriter
    from rexfw.statistics.writers import StandardConsoleMCMCStatisticsWriter
    from rexfw.statistics.writers import StandardFileMCMCStatisticsWriter
    from rexfw.statistics.writers import StandardFileREStatisticsWriter
    from rexfw.statistics.writers import StandardFileREWorksStatisticsWriter

    stats_path = sim_path + 'statistics/'
    mcmc_stats_writers = [StandardConsoleMCMCStatisticsWriter([variable_name],
                                                              ['acceptance rate',
                                                               'stepsize'
                                                               ]),
                          StandardFileMCMCStatisticsWriter(stats_path + '/mcmc_stats.txt',
                                                           [variable_name],
                                                           ['acceptance rate',
                                                            'stepsize'])
                         ]
    re_stats_writers = [StandardConsoleREStatisticsWriter(),
                        StandardFileREStatisticsWriter(stats_path + 're_stats.txt',
                                                       ['acceptance rate'])]

    return mcmc_stats_writers, re_stats_writers

def setup_default_re_master(n_replicas, sim_path, comm):
    '''
    Creates a default :class:`.ExchangeMaster` object for Replica Exchange. This should suffice
    for most applications.

    :param int n_replicas: the number of replicas
    :param str sim_path: the folder where simulation output will be stored
    
    :param comm: a :class:`.AbstractCommunicator` object responsible for communication
                 with the replicas
    :type comm: :class:`.AbstractCommunicator`

    :return: a for all practical purposes sufficient :class:`.ExchangeMaster` object
    :rtype: :class:`.ExchangeMaster`
    '''

    from rexfw.remasters import ExchangeMaster
    from rexfw.statistics import Statistics, REStatistics
    from rexfw.convenience import create_default_RE_params
    from rexfw.convenience.statistics import create_default_works, create_default_heats
    from rexfw.statistics.writers import StandardFileREWorksStatisticsWriter

    variable_name = 'x'
    replica_names = ['replica{}'.format(i) for i in range(1, n_replicas + 1)]
    params = create_default_RE_params(n_replicas)
    
    mcmc_pacc_avgs, re_pacc_avgs, stepsizes = create_default_stats_elements(replica_names,
                                                                            variable_name)
    
    works = create_default_works(replica_names)
    heats = create_default_heats(replica_names)
    mcmc_stats_writers, re_stats_writers = create_default_stats_writers(sim_path,
                                                                        variable_name='x')
    stats = Statistics(elements=mcmc_pacc_avgs + stepsizes, 
                       stats_writer=mcmc_stats_writers)
    works_path = sim_path + 'works/'
    works_writers = [StandardFileREWorksStatisticsWriter(works_path)]
    re_stats = REStatistics(elements=re_pacc_avgs,
                            work_elements=works, heat_elements=heats,
                            stats_writer=re_stats_writers,
                            works_writer=works_writers)
    
    master = ExchangeMaster('master0', replica_names, params, comm=comm, 
                            sampling_statistics=stats, swap_statistics=re_stats)

    return master

def setup_default_replica(init_state, pdf, sampler_class, sampler_params, 
                          output_folder, comm, rank):
    '''
    Creates a default :class:`.Replica` object for replica exchange. This should suffice
    for most applications.

    :param init_state: initial state for the replica
    :type init_state: depends on your application

    :param pdf: a :class:`.AbstractPDF` object which describes the probability density
                the replica will sample
    :type pdf: :class:`.AbstractPDF`

    :param sampler_class: the class of the sampler used to sample from this replica's
                          PDF
    :type sampler_class: :class:`.AbstractSampler`

    :param dict sampler_params: a dict containing additional keyword arguments your
                                sampler might need
                                
    :param str output_folder: the folder where simulation output will be stored
    
    :param comm: a :class:`.AbstractCommunicator` object responsible for communication
                 with the master object
    :type comm: :class:`.AbstractCommunicator`

    :param int rank: the index of this replica, usually 1, 2, ...
    
    :return: a for all practical purposes sufficient :class:`.Replica` object
    :rtype: :class:`.Replica`
    '''

    from rexfw.replicas import Replica
    ## every kind of RE / RENS has its own proposer classes which 
    ## calculate proposal states for exchanges
    from rexfw.proposers.re import REProposer

    ## many objects have names to identify them when 
    ## forwarding messages coming in from the communicators
    ## these are default names required for the functions in the
    ## convenience module to create correct default objects
    replica_name = 'replica{}'.format(rank)
    proposer_name = 'prop{}'.format(rank)
    
    proposer = REProposer(proposer_name)
    ## in principle, we could use several proposers to, e.g., alternate between
    ## RE and RENS
    proposers = {proposer_name: proposer}

    replica = Replica(name=replica_name, 
                      state=init_state, 
                      pdf=pdf,
                      sampler_class=sampler_class,
                      sampler_params=sampler_params,
                      proposers=proposers,
                      output_folder=output_folder,
                      comm=comm)

    return replica

def create_directories(sim_folder):
    '''
    Creates simulation output folders
    '''
    
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
