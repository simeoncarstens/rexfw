import numpy as np
import os, sys
from mpi4py import MPI

from rexfw.communicators.mpi import MPICommunicator
from rexfw.convenience import create_standard_RE_params

mpicomm = MPI.COMM_WORLD
rank = mpicomm.Get_rank()
size = mpicomm.Get_size()

n_replicas = size - 1

sim_name = 'normaltest'

## this is where all simulation output (samples, statistics files, etc.) are stored
outpath = '/tmp/{}_{}replicas/'.format(sim_name, n_replicas)

## communicators are classes which serve as an interface between, say, MPI and the rexfw code
## other communicators could use, e.g., the Python multiprocessing module to
## communicate between the master and the replicas
comm = MPICommunicator()

if rank == 0:

    ## the first process (rank 0) runs an ExchangeMaster, which sends out 
    ## commands / requests to the replica processes, such as "sample", 
    ## "propose exchange states", "accept proposal", etc.

    from rexfw.convenience import setup_default_re_master, create_directories

    create_directories(outpath)
    ## sets up a default RE master object; should be sufficient for all practical purposes
    master = setup_default_re_master(n_replicas, outpath, comm)    
    master.run(10000,                    # number of MCMC samples
               swap_interval=5,          # interval of exchange attempts
               status_interval=50,       # interval with which to print / write out sampling statistics
               dump_interval=200,        # interval with which to dump samples to disk
               samples_folder=outpath + 'samples/',
               dump_step=3               # samples dump step: write out only every i-th sample
        )
    ## send kill request to break from infinite message receiving loop in replicas
    master.terminate_replicas()

else:

    from csb.statistics.pdf import Normal

    ## every process with rank > 0 runs a replica, which does single-chain
    ##  sampling and proposes exchange states
    from rexfw.replicas import Replica
    ## the slaves are relicts; originally I thought them to pass on
    ##  messages from communicators to proposers / replicas, but now
    ## the replicas take care of everything themselves
    from rexfw.slaves import Slave
    ## this is mostly my CSB HMC sampler with a few extra functions for compatibility with rexfw
    from isd2.samplers.hmc import FastHMCSampler
    ## every kind of RE / RENS has its own proposer classes which 
    ## calculate proposal states for exchanges
    from rexfw.proposers import REProposer

    ## many objects have names to identify them when 
    ## forwarding messages coming in from the communicators
    replica_names = ['replica{}'.format(i) for i in range(1, size)]
    proposer_names = ['prop{}'.format(i) for i in range(1, size)]
    
    proposer = REProposer('prop{}'.format(rank))
    proposers = {proposer.name: proposer}

    ## utility function to create sequences with exponentially increasing spacing
    ## between values for, e.g., replica schedules
    def expspace(min, max, a, N):

        g = lambda n:   (max - min) / (np.exp(a*(N-1.0)) - 1.0) * (np.exp(a*(n-1.0)) - 1.0) + float(min)
    
        return np.array(map(g, np.arange(1, N+1)))

    ## create a schedule with exponentially spacing between replica parameters
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
    np.random.seed(rank)
    init_state = np.array([np.random.normal()])

    sampler = FastHMCSampler(pdf=pdf, state=init_state, timestep=hmc_timestep,
                             timestep_adaption_limit=1000, nsteps=hmc_trajectory_length,
                             variable_name='x')
    replica = Replica(name=replica_names[rank-1], 
                      state=init_state, 
                      pdf=pdf,
                      sampler=sampler,
                      proposers=proposers,
                      comm=comm)
    slave = Slave({replica_names[rank-1]: replica}, comm)

    slave.listen()
