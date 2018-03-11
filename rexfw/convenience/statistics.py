'''
Some functions creating default statistics elements
'''

def create_default_MCMC_averages(replica_names, variable_name='x'):
    
    from rexfw.statistics.averages import MCMCAcceptanceRateAverage
    
    mcmc_pacc_avgs = [MCMCAcceptanceRateAverage(replica_name, 'x')
                      for replica_name in replica_names]

    return mcmc_pacc_avgs


def create_default_RE_averages(replica_names):

    from rexfw.statistics.averages import REAcceptanceRateAverage
    
    re_pacc_avgs = [REAcceptanceRateAverage(replica_names[i], replica_names[i+1]) 
                    for i in range(len(replica_names) - 1)]
    
    return re_pacc_avgs

def create_default_works(replica_names):

    from rexfw.statistics.logged_quantities import REWorks

    works = [REWorks(replica_names[i], replica_names[i+1]) for i in range(len(replica_names) - 1)]

    return works

def create_default_heats(replica_names):

    from rexfw.statistics.logged_quantities import REHeats

    heats = [REHeats(replica_names[i], replica_names[i+1]) for i in range(len(replica_names) - 1)]

    return heats

def create_default_stepsizes(replica_names, variable_name='x'):

    from rexfw.statistics.logged_quantities import SamplerStepsize

    stepsizes = [SamplerStepsize(replica_name, variable_name) for replica_name in replica_names]

    return stepsizes
