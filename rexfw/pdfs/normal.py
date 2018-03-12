'''
A normal distribution as an example for the PDF interface
'''

from rexfw.pdfs import AbstractPDF

class Normal(AbstractPDF):

    def __init__(self, mu=0.0, sigma=1.0):
        
        self.mu = mu
        self.sigma = sigma

    def log_prob(self, x):
        
        return -0.5 * (x - self.mu) ** 2 / self.sigma / self.sigma
