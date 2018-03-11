'''
Defines the interface for compatible samplers
'''

from abc import abstractmethod, abstractproperty
from collections import namedtuple


class AbstractSampler(object):

    def __init__(self, pdf, state, variable_name):
        '''
        Arguments:
        - a PDF with the interface defined in AbstractPDF
        - an initial state
        - a string with a name for the variable this object samples from
        '''
        self.pdf = pdf
        self.state = state
        self.variable_name = variable_name

    @abstractmethod
    def sample(self):
        '''
        draws a sample, possibly using self.state (for MCMC)
        '''
        pass

    @abstractproperty
    def last_draw_stats(self):
        '''
        Returns a dictionary of the form
        {self.variable_name: SamplerStats(...)}
        '''
        pass


## this is the object occuring in the dictionary return by
## AbstractSampler.last_draw_stats. statsA,B,C (or similar) are fields
## such as acceptance rate, time step etc.
SampleStats = namedtuple('SamplerStats', 'statsA statsB statsC')
