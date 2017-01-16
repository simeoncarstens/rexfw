import numpy, os, sys
from mpi4py import MPI

from rexfw.communicators.mpi import MPICommunicator
from rexfw.convenience import create_standard_RE_params

mpicomm = MPI.COMM_WORLD
rank = mpicomm.Get_rank()
size = mpicomm.Get_size()

n_replicas = size - 1

sim_name = 'normaltest'

outpath = '/tmp/{}_{}replicas/'.format(sim_name, n_replicas)
os.system('mkdir '+outpath)
samplespath = outpath + 'samples/'
os.system('mkdir '+samplespath)
statspath = outpath + 'statistics/'
os.system('mkdir '+statspath)
workspath = outpath + 'works/'
os.system('mkdir '+workspath)

## communicators are classes which serve as an interface between, say, MPI and the rexfw code
## other communicators could use, e.g., the Python multiprocessing module
comm = MPICommunicator()

## many objects have names to identify them when forwarding messages coming in from the communicators
replica_names = ['replica{}'.format(i) for i in range(1, size)]
proposer_names = ['prop{}'.format(i) for i in range(1, size)]

if rank == 0:

    ## the first process (rank 0) runs an ExchangeMaster, which sends out commands / requests to the rpelica processes, such as "sample", "propose exchange states", "accept proposal", etc.
    from rexfw.remasters import ExchangeMaster
    ## I tried to implement general logging / sampling statistics capabilities. This has become pretty blown-up
    from rexfw.statistics import MCMCSamplingStatistics, REStatistics
    from rexfw.statistics.writers import StandardConsoleMCMCStatisticsWriter, StandardConsoleREStatisticsWriter, StandardFileMCMCStatisticsWriter, StandardFileREStatisticsWriter, StandardFileREWorksStatisticsWriter
    ## in .convenience I have functions which create default parameters
    from rexfw.convenience.statistics import create_standard_averages, create_standard_works, create_standard_stepsizes

    params = create_standard_RE_params(n_replicas)

    local_pacc_avgs, re_pacc_avgs = create_standard_averages(replica_names)
    works = create_standard_works(replica_names)
    stepsizes = create_standard_stepsizes(replica_names)

    stats = MCMCSamplingStatistics(comm, elements=local_pacc_avgs + stepsizes, 
                                   stats_writer=[StandardConsoleMCMCStatisticsWriter(),
                                                 StandardFileMCMCStatisticsWriter(statspath + 'mcmc_stats.txt')])
    re_stats = REStatistics(elements=re_pacc_avgs,work_elements=works, heat_elements=[],
                            stats_writer=[StandardConsoleREStatisticsWriter(),
                                          StandardFileREStatisticsWriter(statspath + 're_stats.txt')])
    
    master = ExchangeMaster('master0', replica_names, params, comm=comm, 
                            sampling_statistics=stats, swap_statistics=re_stats)

    master.run(10000, swap_interval=5, status_interval=50, dump_interval=200, 
               samples_folder=outpath, dump_step=3)
    master.terminate_replicas()

else:

    from csb.statistics.samplers import State
    from csb.statistics.pdf import Normal

    ## every process with rank > 0 runs a replica, which does single-chain sampling and proposes exchange states
    from rexfw.replicas import Replica
    ## the slaves are relicts; originally I thought them to pass on messages from communicators to proposers / replicas, but now the replicas take care of everything themselves
    from rexfw.slaves import Slave
    ## this is mostly my CSB HMC sampler with a few extra functions for compatibility with rexfw
    from rexfw.samplers.hmc import CompatibleHMCSampler
    ## every kind of RE / RENS has its own proposer classes which calculate proposal states
    from rexfw.proposers import REProposer
    
    proposer = REProposer('prop{}'.format(rank))
    proposers = {proposer.name: proposer}

    def expspace(min, max, a, N):

        g = lambda n: (max - min) / (numpy.exp(a*(N-1.0)) - 1.0) * (numpy.exp(a*(n-1.0)) - 1.0) + float(min)
    
        return numpy.array(map(g, numpy.arange(1, N+1)))

    schedule = expspace(1, 0, 0.2, size)
    if rank == 1:
        print schedule
    hmc_timesteps = expspace(0.1, 1.0, 0.2, size)

    hmc_timestep = hmc_timesteps[rank-1]
    hmc_trajectory_length = 100

    class MyNormal(Normal):

        def gradient(self, x, t=0.0):

            return (x - self['mu']) / self['sigma'] / self['sigma']
    
    pdf = MyNormal(sigma=float(rank))
    numpy.random.seed(rank)
    init_state = numpy.random.normal()
    init_state = State(numpy.array([init_state]))
    
    replica = Replica(name=replica_names[rank-1], 
                      state=init_state, 
                      pdf=pdf,
                      pdf_params = {}
                      sampler_class=CompatibleHMCSampler,
                      sampler_params={'timestep': hmc_timestep,
                                      'adapt_timestep': True,
                                      'nsteps': hmc_trajectory_length},
                      proposers=proposers,
                      comm=comm)
    slave = Slave({replica_names[rank-1]: replica}, comm)

    slave.listen()
