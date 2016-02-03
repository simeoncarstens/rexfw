import numpy
from langevin import LTMDRENS, LTMDRENSSwapParameterInfo
from csb.statistics.samplers import State

import numpy
from numpy import sqrt
from csb.io.plots import Chart
# from csb.statistics.pdf import Normal
from csb.statistics.samplers import State
from csb.statistics.samplers.mc.multichain import ThermostattedMDRENSSwapParameterInfo
from csb.statistics.samplers.mc.multichain import ThermostattedMDRENS, AlternatingAdjacentSwapScheme, ReplicaExchangeMC
from csb.statistics.samplers.mc.singlechain import HMCSampler
from rexfw.test.pdfs import MyNormal

# Pick some initial state for the different Markov chains:
initial_state = State(numpy.array([1.]))

# Set standard deviations:
std_devs = [1./sqrt(7), 1./sqrt(5), 1. / sqrt(3), 1.]

pdfs = [MyNormal(sigma=std_dev) for std_dev in std_devs]

# Set HMC timesteps and trajectory length:
hmc_timesteps = [0.6, 0.6, 0.6, 0.6]
hmc_trajectory_length = 20
hmc_gradients = [pdf.gradient for pdf in pdfs]

# Set parameters for the thermostatted RENS algorithm:
rens_trajectory_length = 15
rens_timesteps = [0.3, 0.5, 0.7]

# # Set interpolation gradients as a function of the work parameter l:
# rens_gradients = [lambda q, l, i=i: l * pdfs[i+1].gradient(q) + (1.0 - l) * pdfs[i].gradient(q) 
#                           for i in range(len(pdfs)-1)]

from rexfw.proposers import ParamInterpolationPDF
from collections import namedtuple
P = namedtuple('P', 'n_steps timestep pdf_params')
ipdfs = [ParamInterpolationPDF(MyNormal(), 
                               P(rens_trajectory_length, rens_timesteps[i], 
                                 {'sigma': (std_devs[i], std_devs[i+1])})) 
         for i in range(len(pdfs) - 1)]
rens_gradients = [lambda x, l, i=i: ipdfs[i].gradient(x, l*rens_timesteps[i]*rens_trajectory_length) 
                  for i, pdf in enumerate(ipdfs)]

# Initialize HMC samplers:
# samplers = [HMCSampler(Normal(sigma=std_devs[i]), initial_state, hmc_gradients[i], hmc_timesteps[i],
#                        hmc_trajectory_length) for i in range(len(std_devs))]

from csb.statistics.samplers.mc.singlechain import RWMCSampler
samplers = [RWMCSampler(MyNormal(sigma=std_devs[i]), 
                        State(numpy.array([float(i+1)])), 
                        0.7) for i in range(len(std_devs))]

# Create swap parameter objects:
params = [LTMDRENSSwapParameterInfo(samplers[i], samplers[i+1], rens_timesteps[i],
                                    rens_trajectory_length, rens_gradients[i], gamma=1.0)
          for i in range(len(samplers) - 1)]

# Initialize thermostatted RENS algorithm:
algorithm = LTMDRENS(samplers, params)

# algorithm = ReplicaExchangeMC(samplers, params)

# Initialize swapping scheme:
swapper = AlternatingAdjacentSwapScheme(algorithm)

# Initialize empty list which will store the samples:
states = []
for i in range(5):#15000):
    if i % 5 == 0:
        # print "swap"
        swapper.swap_all()
    states.append(algorithm.sample())

# Print acceptance rates:
print('HMC acceptance rates:', [s.acceptance_rate for s in samplers])
print('swap acceptance rates:', algorithm.acceptance_rates)

# # Create and plot histogram for first sampler and numpy.random.normal reference:
# chart = Chart()
# rawstates = [state[0].position[0] for state in states]
# chart.plot.hist([numpy.random.normal(size=5000, scale=std_devs[0]), rawstates], bins=30, normed=True)
# chart.plot.legend(['numpy.random.normal', 'RENS + HMC'])
# chart.show()
