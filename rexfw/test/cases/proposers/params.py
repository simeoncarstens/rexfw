'''
'''

from rexfw.proposers.params import AbstractProposerParams


class MockProposerParams(AbstractProposerParams):

    def __init__(self):

        self.reverse_events = 0

    def reverse(self):

        self.reverse_events += 1
