import numpy, os, sys
sys.path.append(os.path.expanduser('~/projects/'))

from mpi4py import MPI

from rexfw.communicators.mpi import MPICommunicator

mpicomm = MPI.COMM_WORLD
rank = mpicomm.Get_rank()
size = mpicomm.Get_size()

n_replicas = size - 1

comm = MPICommunicator()

replica_names = ['replica{}'.format(i) for i in range(1, size)]
proposer_names = ['prop{}'.format(i) for i in range(1, size)]

if rank == 0:

    from rexfw.remasters import StandardReplicaExchangeMaster
    from rexfw.statistics import MCMCSamplingStatistics, REStatistics
    from rexfw.statistics.averages import AcceptanceRateAverage

    pacc_avg = AcceptanceRateAverage()
    local_pacc_avgs = {'sampler_{}'.format(r): {'p_acc': AcceptanceRateAverage()} for r in replica_names}
    re_pacc_avgs = {'{0}_{1}'.format(r1,r2): {'p_acc': AcceptanceRateAverage()} for r1 in replica_names for r2 in replica_names}
    stats = MCMCSamplingStatistics(comm, averages=local_pacc_avgs)
    re_stats = REStatistics(averages=re_pacc_avgs)
    master = StandardReplicaExchangeMaster('master0', replica_names, comm=comm, 
                                           sampling_statistics=stats, swap_statistics=re_stats)

    master.run(1100, swap_interval=10, status_interval=1000, dump_interval=1000, 
               samples_folder='/baycells/scratch/carstens/test/', dump_step=1)
    master.terminate_replicas()

    print "RWMC p_acc:", master.sampling_statistics.averages['sampler_replica1']['p_acc'].value
    print "r1 r2 p_acc:", master.swap_statistics.averages['replica1_replica2']['p_acc']

else:

    from csb.statistics.samplers import State
    from csb.statistics.pdf import Normal
    
    from rexfw.replicas import Replica
    from rexfw.slaves import Slave
    from rexfw.samplers.rwmc import CompatibleRWMCSampler, RWMCSampleStats
    from rexfw.proposers import REProposer, LMDRENSProposer

    class MyNormal(Normal):

        def log_prob(self, x):
            return super(MyNormal, self).log_prob(x[0])

        def gradient(self, x):
            return x / self['sigma'] / self['sigma']
    
    proposer = REProposer('prop{}'.format(rank), comm)
    # proposer = LMDRENSProposer(proposer_names[rank-1], comm)
    proposers = {proposer.name: proposer}

    numpy.random.seed(rank)

    sigmas = numpy.linspace(1,100.1, size)
    replica = Replica(replica_names[rank-1], State(numpy.random.normal(size=1)), 
                      MyNormal(sigma=sigmas[rank - 1]), {}, CompatibleRWMCSampler, 
                      {'stepsize': 0.75}, proposers, comm)
    slave = Slave({replica_names[rank-1]: replica}, comm)

    slave.listen()
