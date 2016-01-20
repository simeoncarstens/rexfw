import numpy, os, sys
# sys.path.append(os.path.expanduser('~/projects/'))

from mpi4py import MPI

from rexfw.communicators.mpi import MPICommunicator
from rexfw.convenience import create_standard_HMCStepRENS_params, create_standard_LMDRENS_params, create_standard_RE_params

mpicomm = MPI.COMM_WORLD
rank = mpicomm.Get_rank()
size = mpicomm.Get_size()

n_replicas = size - 1

comm = MPICommunicator()

replica_names = ['replica{}'.format(i) for i in range(1, size)]
proposer_names = ['prop{}'.format(i) for i in range(1, size)]

sigmas = 1.0 / numpy.sqrt(numpy.array([5,3,1]))
schedule = {'sigma': sigmas}
timesteps = [0.3, 0.5]

if rank == 0:

    from rexfw.remasters import ExchangeMaster
    from rexfw.statistics import MCMCSamplingStatistics, REStatistics
    from rexfw.convenience.statistics import create_standard_averages

    # params = create_standard_HMCStepRENS_params(schedule, 20, timesteps)
    # params = create_standard_RE_params(n_replicas)
    params = create_standard_LMDRENS_params(schedule, 15, timesteps, 1.0)

    
    local_pacc_avgs, re_pacc_avgs = create_standard_averages(replica_names)
    stats = MCMCSamplingStatistics(comm, averages=local_pacc_avgs)
    re_stats = REStatistics(averages=re_pacc_avgs)
    master = ExchangeMaster('master0', replica_names, params, comm=comm, 
                            sampling_statistics=stats, swap_statistics=re_stats)

    master.run(5000, swap_interval=5, status_interval=1000, dump_interval=100000, 
               samples_folder='/baycells/scratch/carstens/test/', dump_step=1)
    master.terminate_replicas()

    print "MC p_acc:", 
    for x in range(1, size):
        p = master.sampling_statistics.averages['sampler_replica{}'.format(x)]['p_acc'].value
        print "{:.2f}".format(p), 
    print

    print "RE(NS) p_acc:",
    for x in range(1, size - 1):
        pass

        p = master.swap_statistics.averages['replica{}_replica{}'.format(x, x+1)]['p_acc'].value
        print "{:.2f}".format(p), 

    from cPickle import dump
    dump(master.swap_statistics.elements, open('/tmp/stats.pickle','w'))

else:

    from csb.statistics.samplers import State
    from csb.statistics.pdf import Normal
    
    from rexfw.replicas import Replica
    from rexfw.slaves import Slave
    from rexfw.samplers.rwmc import CompatibleRWMCSampler
    from rexfw.samplers.hmc import CompatibleHMCSampler
    from rexfw.proposers import REProposer, LMDRENSProposer, HMCStepRENSProposer, MDRENSProposer

    from rexfw.test.pdfs import MyNormal
    
    # proposer = REProposer('prop{}'.format(rank), comm)

    # proposer = MDRENSProposer(proposer_names[rank-1], comm)
    
    proposer = LMDRENSProposer(proposer_names[rank-1], comm)

    # proposer = HMCStepRENSProposer(proposer_names[rank-1], comm)

    proposers = {proposer.name: proposer}

    hmc_timesteps = [0.6, 0.6, 0.6]
    hmc_trajectory_length = 20

    pdf = MyNormal(sigma=sigmas[rank-1])
    replica = Replica(replica_names[rank-1], State(numpy.array([float(rank)])), 
                      pdf, {}, CompatibleRWMCSampler,
                      {'stepsize': 0.7},
                       proposers, comm)
    slave = Slave({replica_names[rank-1]: replica}, comm)

    slave.listen()
