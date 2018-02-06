'''
'''

import numpy

from csb.statistics.pdf import Normal


class MyNormal(Normal):

    def log_prob(self, x):

        return super(MyNormal, self).log_prob(x[0]) + numpy.log(numpy.sqrt(2.0 * numpy.pi) * self['sigma'])

    def gradient(self, x, t=0.0):

        return x / self['sigma'] / self['sigma']
    


    
