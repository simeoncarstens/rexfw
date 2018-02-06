##!/c5/shared/Python/2.7.3-shared/bin/python -u
import numpy
from csb.statistics.samplers import State, EnsembleState
from ox.structure import get_coords
from protlib import *
from copy import deepcopy
import sys, os
from cPickle import dump, load
from csb.statistics.samplers.mc.multichain import AlternatingAdjacentSwapScheme
from fastcode import FastHMCSampler
from langevin import *
from isdhmcrens import ISDHMCRENSSwapParameterInfo, FastISDHMCRENS, ISDHMCRENS

from cPickle import load
f = open('/baycells/home/carstens/simulations/multiplicity/noes/ubq_work_ref_new_initial_states_and_steps_csbstates.pickle')
states, timesteps = load(f)
timesteps = numpy.array(timesteps)
f.close()

path = '~'
pdbfile = path + '/pdbfiles/1ubq_protonated_whatif_iupac.pdb'
datafile = path + '/data/ubq/nonredundant.xml'

posti = create_posterior(pdbfile=pdbfile, datafile=datafile)
# posti = load(open('/tmp/test.pcikel'))
pdf = ISDWrapper(1.0, 1.0, posti)

traj_length = 20
it = '0'

outdir = "/tmp/"
os.system("mkdir "+outdir+str(traj_length))
os.system("mkdir "+outdir+str(traj_length)+"/"+it)
outpath = outdir+str(traj_length)+"/"+it+"/"
statsfile = outpath + "stats.txt"
paccfile = outpath + "pacc.txt"
statesfile = outpath + "ensemble.pickle"
worksfile = outpath + "works.pickle"
timestepsfile = outpath + "timesteps.pickle"

timesteps = numpy.array(timesteps[:3])
lambda_values = lambda_values[:3]
q_values = q_values[:3]
states = states[:3]

# Set parameters for HMC equilibrium sampling
eq_hmc_traj_length = 25
eq_hmc_timesteps = timesteps

# Initialize HMC samplers:
s_pdfs = [deepcopy(pdf) for i in range(len(timesteps))]
for i in range(len(s_pdfs)):
    s_pdfs[i].l = lambda_values[i]
    s_pdfs[i].q = q_values[i]

samplers = [FastHMCSampler(s_pdfs[i], State(states[i].position), s_pdfs[i].gradient, eq_hmc_timesteps[i],
            eq_hmc_traj_length) for i in range(len(s_pdfs))]

#### RENS parameters ####
rens_traj_length = traj_length
im_pdfs = [LambdaISDWrapper((lambda_values[i], q_values[i]), (lambda_values[i+1], q_values[i+1]), posti) 
           for i in range(len(lambda_values) - 1)]

params = [LTMDRENSSwapParameterInfo(samplers[i], samplers[i+1], timestep=timesteps[i+1] / 5.0, 
                                    gradient=im_pdfs[i].gradient, traj_length=rens_traj_length, gamma=0.01) 
                                    for i in range(len(lambda_values) - 1)]


from csb.statistics.samplers.mc.multichain import ThermostattedMDRENSSwapParameterInfo, ThermostattedMDRENS
params = [ThermostattedMDRENSSwapParameterInfo(samplers[i], samplers[i+1], timestep=timesteps[i+1] / 50.0, 
          gradient=im_pdfs[i].gradient, traj_length=rens_traj_length, collision_probability=0.1, collision_interval=1) 
                                    for i in range(len(lambda_values) - 1)]

params = [ISDHMCRENSSwapParameterInfo(samplers[i], samplers[i+1], timesteps[i+1], nsteps=4, rens_traj_length=rens_traj_length) for i in range(len(samplers) - 1)]


for i, p in enumerate(params):
    p.index = i
    
# Initialize Langevin-RENS algorithm:

# algorithm = LTMDRENS(samplers, params)

# algorithm = ThermostattedMDRENS(samplers, params)

algorithm = ISDHMCRENS(samplers, params)

# Initialize swapping scheme:
swapper = AlternatingAdjacentSwapScheme(algorithm)

# Initialize statistics class
stats = ProteinStatistics(algorithm, pdbfile, posti, statsfile)

# Initialize empty list which will store the samples:
# states = []
nsamples = 3

for i in range(nsamples):
    if i % 5 == 0:
        swapper.swap_all()
    else:
        algorithm.sample()
        


if False:
    for i in range(3):
        print states[i].position.sum(), s_pdfs[i].gradient(numpy.ones(370), 0.0).sum()


if False:
    for i in range(2):
        print im_pdfs[i].gradient(numpy.ones(370), 0.0).sum(), im_pdfs[i].gradient(numpy.ones(370), 1.0).sum()
