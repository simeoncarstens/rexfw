import numpy, os, sys
sys.path.append(os.path.expanduser('~/projects/'))

from mpi4py import MPI

from rexfw.communicators.mpi import MPICommunicator
from rexfw.convenience import create_standard_HMCStepRENS_params, create_standard_LMDRENS_params

mpicomm = MPI.COMM_WORLD
rank = mpicomm.Get_rank()
size = mpicomm.Get_size()

n_replicas = size - 1

comm = MPICommunicator()

replica_names = ['replica{}'.format(i) for i in range(1, size)]
proposer_names = ['prop{}'.format(i) for i in range(1, size)]

sigmas = numpy.linspace(1,3, n_replicas)
schedule = {'sigma': sigmas}
timesteps = numpy.linspace(0.01, 0.1, n_replicas - 1)

if rank == 0:

    from rexfw.remasters import ExchangeMaster
    from rexfw.statistics import MCMCSamplingStatistics, REStatistics
    from rexfw.convenience.statistics import create_standard_averages

    # params = create_standard_HMCStepRENS_params(schedule, 20, timesteps)
    params = create_standard_LMDRENS_params(schedule, 200, timesteps, 0.01)

    local_pacc_avgs, re_pacc_avgs = create_standard_averages(replica_names)
    stats = MCMCSamplingStatistics(comm, averages=local_pacc_avgs)
    re_stats = REStatistics(averages=re_pacc_avgs)
    master = ExchangeMaster('master0', replica_names, params, comm=comm, 
                            sampling_statistics=stats, swap_statistics=re_stats)

    master.run(1100, swap_interval=10, status_interval=1000, dump_interval=10000, 
               samples_folder='/baycells/scratch/carstens/test/', dump_step=1)
    master.terminate_replicas()

    print "RWMC p_acc:", master.sampling_statistics.averages['sampler_replica1']['p_acc'].value
    print "r1 r2 p_acc:", master.swap_statistics.averages['replica1_replica2']['p_acc']
    from cPickle import dump; dump(master.swap_statistics.elements, open('/tmp/stats.pickle','w'))

else:

    from csb.statistics.samplers import State
    from csb.statistics.pdf import Normal
    
    from rexfw.replicas import Replica
    from rexfw.slaves import Slave
    from rexfw.samplers.rwmc import CompatibleRWMCSampler, RWMCSampleStats
    from rexfw.proposers import REProposer, LMDRENSProposer, HMCStepRENSProposer

    class MyNormal(Normal):

        def log_prob(self, x):
            return super(MyNormal, self).log_prob(x[0])

        def gradient(self, x):
            return x / self['sigma'] / self['sigma']
    
    proposer = REProposer('prop{}'.format(rank), comm)
    proposer = LMDRENSProposer(proposer_names[rank-1], comm)
    # proposer = HMCStepRENSProposer(proposer_names[rank-1], comm)
    proposers = {proposer.name: proposer}

    numpy.random.seed(rank)

    replica = Replica(replica_names[rank-1], State(numpy.random.normal(size=1)), 
                      MyNormal(sigma=sigmas[rank - 1]), {}, CompatibleRWMCSampler, 
                      {'stepsize': 0.75}, proposers, comm)
    slave = Slave({replica_names[rank-1]: replica}, comm)

    slave.listen()
