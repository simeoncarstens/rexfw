import numpy, os, sys
# sys.path.append(os.path.expanduser('~/projects/'))

from mpi4py import MPI

from rexfw.communicators.mpi import MPICommunicator
from rexfw.convenience import create_standard_HMCStepRENS_params, create_standard_LMDRENS_params, create_standard_RE_params, create_standard_AMDRENS_params

mpicomm = MPI.COMM_WORLD
rank = mpicomm.Get_rank()
size = mpicomm.Get_size()

n_replicas = size - 1

comm = MPICommunicator()

replica_names = ['replica{}'.format(i) for i in range(1, size)]
proposer_names = ['prop{}'.format(i) for i in range(1, size)]

sigmas = 1.0 / numpy.sqrt(numpy.array([7,5,3,1]))
# sigmas = 1 / sigmas ** 2
schedule = {'sigma': sigmas}
timesteps = [0.3, 0.5, 0.7]

if rank == 0:

    print 1.0 / sigmas ** 2
    from rexfw.remasters import ExchangeMaster
    from rexfw.statistics import MCMCSamplingStatistics, REStatistics
    from rexfw.statistics.writers import ConsoleStatisticsWriter, StandardConsoleMCMCStatisticsWriter, StandardConsoleREStatisticsWriter, StandardFileMCMCStatisticsWriter, StandardFileREStatisticsWriter, StandardFileREWorksStatisticsWriter
    from rexfw.convenience.statistics import create_standard_averages, create_standard_works

    # params = create_standard_HMCStepRENS_params(schedule=schedule, 
    #                                             n_intermediate_steps=5,
    #                                             timesteps=timesteps,
    #                                             n_hmc_iterations=1,
    #                                             hmc_traj_length=1)
    # params = create_standard_RE_params(n_replicas)
    params = create_standard_LMDRENS_params(schedule, 15, timesteps, 1.0)
    # params = create_standard_AMDRENS_params(schedule, 15, timesteps)
    
    local_pacc_avgs, re_pacc_avgs = create_standard_averages(replica_names)
    works = create_standard_works(replica_names)

    # from rexfw.statistics import SamplerStepsize
    # local_sampler_elements = [SamplerStepsize('sampler_replica{}'.format(i)) for i in range(1, size)]

    stats = MCMCSamplingStatistics(comm, elements=local_pacc_avgs,
                                   stats_writer=[StandardConsoleMCMCStatisticsWriter(),
                                                 StandardFileMCMCStatisticsWriter('/tmp/out.txt')])
    re_stats = REStatistics(name='REStatistics', elements=re_pacc_avgs, work_elements=works,
                            stats_writer=[StandardConsoleREStatisticsWriter(),
                                          StandardFileREStatisticsWriter('/tmp/out_re.txt')],
                            works_writer=[StandardFileREWorksStatisticsWriter('/tmp/')])
    master = ExchangeMaster('master0', replica_names, params, comm=comm, 
                            sampling_statistics=stats, swap_statistics=re_stats)

    master.run(5,#15000,
               swap_interval=5, status_interval=100, dump_interval=100000, 
               samples_folder='/baycells/scratch/carstens/test/', dump_step=1)
    master.terminate_replicas()
    
    # print "MC p_acc:", 
    # for x in range(1, size):
    #     p = master.sampling_statistics.averages['sampler_replica{}'.format(x)]['p_acc'].value
    #     print "{:.2f}".format(p), 
    # print

    # print "RE(NS) p_acc:",
    # for x in range(1, size - 1):
    #     pass

    #     p = master.swap_statistics.averages['replica{}_replica{}'.format(x, x+1)]['p_acc'].value
    #     print "{:.2f}".format(p), 

    # from cPickle import dump
    # dump((master.swap_statistics.elements, master.swap_statistics.averages), open('/tmp/stats.pickle','w'))

else:

    from csb.statistics.samplers import State
    from csb.statistics.pdf import Normal
    
    from rexfw.replicas import Replica
    from rexfw.slaves import Slave
    from rexfw.samplers.rwmc import CompatibleRWMCSampler
    from rexfw.samplers.hmc import CompatibleHMCSampler
    from rexfw.proposers import REProposer, LMDRENSProposer, HMCStepRENSProposer, AMDRENSProposer

    from rexfw.test.pdfs import MyNormal
    
    # proposer = REProposer('prop{}'.format(rank))

    # proposer = MDRENSProposer(proposer_names[rank-1])
    
    proposer = LMDRENSProposer(proposer_names[rank-1])

    # proposer = HMCStepRENSProposer(proposer_names[rank-1])

    # proposer = AMDRENSProposer(proposer_names[rank-1])

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
