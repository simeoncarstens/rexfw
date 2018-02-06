import numpy, os, sys
# sys.path.append(os.path.expanduser('~/projects/'))

from mpi4py import MPI

from rexfw.communicators.mpi import MPICommunicator
from rexfw.convenience import create_standard_HMCStepRENS_params, create_standard_LMDRENS_params, create_standard_RE_params, create_standard_AMDRENS_params

from protlib import lambda_values, q_values

mpicomm = MPI.COMM_WORLD
rank = mpicomm.Get_rank()
size = mpicomm.Get_size()

n_replicas = size - 1

from cPickle import load
f = open('/baycells/home/carstens/simulations/multiplicity/noes/ubq_work_ref_new_initial_states_and_steps_csbstates.pickle')
states, timesteps = load(f)
timesteps = numpy.array(timesteps)
f.close()

timesteps = numpy.array(timesteps[:4])
lambda_values = lambda_values[:4]
q_values = q_values[:4]
states = states[:4]

sim_name = 'test'

outpath = '/baycells/scratch/carstens/rens/isdubq/{}_{}replicas/'.format(sim_name, n_replicas)
os.system('mkdir '+outpath)
samplespath = outpath + 'samples/'
os.system('mkdir '+samplespath)
statspath = outpath + 'statistics/'
os.system('mkdir '+statspath)
workspath = outpath + 'works/'
os.system('mkdir '+workspath)

## copy this file and current REXFW version to output directory
srcdir = outpath+'src/'
os.system('mkdir '+srcdir)
import inspect
os.system('cp {} {}'.format(inspect.getfile(inspect.currentframe()), srcdir))
os.system('cp -r {} {}'.format('/baycells/home/carstens/projects/rexfw/',
                               srcdir))


comm = MPICommunicator()

replica_names = ['replica{}'.format(i) for i in range(1, size)]
proposer_names = ['prop{}'.format(i) for i in range(1, size)]

schedule = {'lammda': lambda_values, 'q': q_values}

if rank == 0:

    from rexfw.remasters import ExchangeMaster
    from rexfw.statistics import MCMCSamplingStatistics, REStatistics
    from rexfw.statistics.writers import StandardConsoleMCMCStatisticsWriter, StandardConsoleREStatisticsWriter, StandardFileMCMCStatisticsWriter, StandardFileREStatisticsWriter, StandardFileREWorksStatisticsWriter
    from rexfw.convenience.statistics import create_standard_averages, create_standard_works, create_standard_stepsizes

    params = create_standard_HMCStepRENS_params(schedule, 
                                                n_intermediate_steps=20, 
                                                timesteps=timesteps[1:],
                                                n_hmc_iterations=1, 
                                                hmc_traj_length=4)
    # params = create_standard_RE_params(n_replicas)
    # params = create_standard_LMDRENS_params(schedule, 20, timesteps[1:] / 5.0, 0.01)
    # params = create_standard_AMDRENS_params(schedule, 20, timesteps[1:] / 50.0)
    
    local_pacc_avgs, re_pacc_avgs = create_standard_averages(replica_names)
    works = create_standard_works(replica_names)
    stepsizes = create_standard_stepsizes(replica_names)

    stats = MCMCSamplingStatistics(comm, elements=local_pacc_avgs + stepsizes, 
                                   stats_writer=[StandardConsoleMCMCStatisticsWriter(),
                                                 StandardFileMCMCStatisticsWriter(statspath + 'mcmc_stats.txt')])
    re_stats = REStatistics(elements=re_pacc_avgs, work_elements=works,
                            stats_writer=[StandardConsoleREStatisticsWriter(),
                                          StandardFileREStatisticsWriter(statspath + 're_stats.txt')],
                            works_writer=[StandardFileREWorksStatisticsWriter(workspath)])
    
    master = ExchangeMaster('master0', replica_names, params, comm=comm, 
                            sampling_statistics=stats, swap_statistics=re_stats)

    master.run(3, swap_interval=5, status_interval=1000, dump_interval=500, 
               samples_folder=outpath, dump_step=3)
    master.terminate_replicas()

else:

    from csb.statistics.samplers import State
    
    from rexfw.replicas import Replica
    from rexfw.slaves import Slave
    from rexfw.samplers.hmc import CompatibleHMCSampler
    from rexfw.proposers import REProposer, LMDRENSProposer, HMCStepRENSProposer, AMDRENSProposer

    import os
    os.chdir('/baycells/home/carstens/projects/rens/py/')

    from pdfs import UBQISDPosterior, OldISDInterpolatingPDF
    
    # proposer = REProposer('prop{}'.format(rank))

    # proposer = MDRENSProposer(proposer_names[rank-1])

    
    # proposer = LMDRENSProposer(proposer_names[rank-1], OldISDInterpolatingPDF)

    proposer = HMCStepRENSProposer(proposer_names[rank-1], OldISDInterpolatingPDF)

    # proposer = AMDRENSProposer(proposer_names[rank-1], OldISDInterpolatingPDF)

    proposers = {proposer.name: proposer}

    hmc_timestep = timesteps[rank-1]
    hmc_trajectory_length = 25

    pdf = UBQISDPosterior(lammda=schedule['lammda'][rank-1], 
                          q=schedule['q'][rank-1])                           

    ## TODO: why the hell can't I use the posterior of the PDF? When I do.
    ##       LambdaISDWrapper.calc_gradients() gives different results for
    ##       identical torsion angles during forward and backward trajectory
    
    from cPickle import load
    p = load(open('/tmp/posterior.pickle'))
    proposer.posterior = p
    # proposer.posterior = pdf._isdwrapper.posterior


    replica = Replica(replica_names[rank-1], states[rank-1], 
                      pdf, {}, CompatibleHMCSampler,
                      {'timestep': timesteps[rank-1],
                       'nsteps': hmc_trajectory_length,
                       'adapt_timestep': True},
                       proposers, comm)
    slave = Slave({replica_names[rank-1]: replica}, comm)

    slave.listen()
