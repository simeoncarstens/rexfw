'''
'''


def create_standard_averages(replica_names):

    from rexfw.statistics.averages import REAcceptanceRateAverage, MCMCAcceptanceRateAverage
    
    local_pacc_avgs = [MCMCAcceptanceRateAverage('sampler_'+r) for r in replica_names]
    re_pacc_avgs = [REAcceptanceRateAverage(replica_names[i], replica_names[i+1]) 
                    for i in range(len(replica_names) - 1)]
    
    return local_pacc_avgs, re_pacc_avgs


def create_standard_works(replica_names):

    from rexfw.statistics.logged_quantities import REWorks

    works = [REWorks(replica_names[i], replica_names[i+1]) for i in range(len(replica_names) - 1)]

    return works

def create_standard_heats(replica_names):

    from rexfw.statistics.logged_quantities import REHeats

    heats = [REHeats(replica_names[i], replica_names[i+1]) for i in range(len(replica_names) - 1)]

    return heats

def create_standard_stepsizes(replica_names):

    from rexfw.statistics.logged_quantities import SamplerStepsize

    return [SamplerStepsize('sampler_'+r) for r in replica_names]
