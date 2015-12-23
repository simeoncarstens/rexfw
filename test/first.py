import numpy, os, sys
sys.path.append(os.path.expanduser('~/projects/'))

from mpi4py import MPI

from rexfw.communicators.mpi import MPICommunicator

mpicomm = MPI.COMM_WORLD
rank = mpicomm.Get_rank()
size = mpicomm.Get_size()

n_replicas = size - 1

comm = MPICommunicator()

if rank == 0:

    from rexfw.remasters import ReplicaExchangeMaster
    from rexfw.statistics import MCMCSamplingStatistics
    from rexfw.statistics.averages import AcceptanceRateAverage

    pacc_avg = AcceptanceRateAverage()
    local_pacc_avgs = {'sampler{}'.format(i): {'p_acc': AcceptanceRateAverage()} for i in xrange(1,n_replicas + 1)}
    stats = MCMCSamplingStatistics(n_replicas, comm)
    master = ReplicaExchangeMaster('master0', n_replicas, comm=comm, sampling_statistics=stats)

    master.run(5000, swap_interval=10, status_interval=1000, dump_interval=1000, 
               samples_folder='/baycells/scratch/carstens/test/', dump_step=1)
    master.terminate_replicas()

    print master.sampling_statistics.averages['sampler1']['p_acc'].value

else:

    from csb.statistics.samplers import State
    from csb.statistics.pdf import Normal
    
    from rexfw.replicas import Replica
    from rexfw.slaves import Slave
    from rexfw.samplers.rwmc import CompatibleRWMCSampler, RWMCSampleStats
    
    replica = Replica('replica{}'.format(rank), State(numpy.random.normal(size=1)), 
                      Normal(), {}, CompatibleRWMCSampler, 
                      {'stepsize': 0.75}, comm, rank)
    slave = Slave({'replica{}'.format(rank): replica}, comm)

    slave.listen()
