'''
Defines the interface for compatible PDFs:
all they need is a log_prob method which returns the
log-probability of a state
'''

from abc import abstractmethod

class AbstractPDF(object):

    @abstractmethod
    def log_prob(self, x):
        pass
