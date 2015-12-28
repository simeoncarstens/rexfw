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

if rank == 0:

    from rexfw.remasters import ReplicaExchangeMaster
    from rexfw.statistics import MCMCSamplingStatistics
    from rexfw.statistics.averages import AcceptanceRateAverage

    pacc_avg = AcceptanceRateAverage()
    local_pacc_avgs = {'sampler_{}'.format(r): {'p_acc': AcceptanceRateAverage()} for r in replica_names}
    stats = MCMCSamplingStatistics(comm, averages=local_pacc_avgs)
    master = ReplicaExchangeMaster('master0', replica_names, comm=comm, sampling_statistics=stats)

    master.run(5000, swap_interval=10, status_interval=1000, dump_interval=1000, 
               samples_folder='/baycells/scratch/carstens/test/', dump_step=1)
    master.terminate_replicas()

    print "p_acc:", master.sampling_statistics.averages['sampler_replica2']['p_acc'].value

else:

    from csb.statistics.samplers import State
    from csb.statistics.pdf import Normal
    
    from rexfw.replicas import Replica
    from rexfw.slaves import Slave
    from rexfw.samplers.rwmc import CompatibleRWMCSampler, RWMCSampleStats
    from rexfw.exchangers import ReplicaExchanger
    from rexfw.proposers import GeneralREProposer

    proposer = GeneralREProposer('reprop{}'.format(rank), comm)
    exchangers = {'rexex{}'.format(rank): ReplicaExchanger(proposer, comm)}
    replica = Replica('replica{}'.format(rank), State(numpy.random.normal(size=1)), 
                      Normal(), {}, CompatibleRWMCSampler, 
                      {'stepsize': 0.75}, exchangers, comm)
    slave = Slave({'replica{}'.format(rank): replica}, comm)

    slave.listen()
