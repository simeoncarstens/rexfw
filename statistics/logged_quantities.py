'''
Logable (?) quantities
'''

from collections import OrderedDict


class LoggedQuantity(object):

    def __init__(self, name):

        self._values = OrderedDict()
        self._default_value = None
        self.step = None
        self._name = name
        self.origins = []

    def __getitem__(self, step):
        return self.values[str(step)] if step != -1 else self.current_value

    @property
    def values(self):
        return self._values

    @property
    def name(self):
        return self._name

    @property
    def current_value(self):
        return self.values[next(reversed(self.values))] if len(self.values) > 0 else self._default_value

    def update(self, step, value):

        self._values.update(**{str(step): value})


class SamplerStepsize(LoggedQuantity):

    def __init__(self, sampler_name):

        super(SamplerStepsize, self).__init__('stepsize')
        self.origins.append(sampler_name)

    def __repr__(self):

        return 'stepsize {}: {}'.format(self.origins[0], self.current_value)
        

class MCMCMoveAccepted(LoggedQuantity):

    def __init__(self, sampler_name):

        super(MCMCMoveAccepted, self).__init__('mcmc_accepted')
        self.origins.append(sampler_name)
        self._default_value = None

    def __repr__(self):

        return 'accepted {}: {}'.format(self.origins[0], self.current_value)


class REMoveAccepted(LoggedQuantity):

    def __init__(self, replica1, replica2):

        super(REMoveAccepted, self).__init__('re_accepted')
        self.origins.append(replica1)
        self.origins.append(replica2)
        self.__default_value = None
    
    def __repr__(self):

        return 'accepted {} <> {}: {}'.format(self.origins[0], self.origins[1], 
                                              self.value)


class REWorks(LoggedQuantity):

    def __init__(self, replica1, replica2):

        import numpy 
        
        super(REWorks, self).__init__('re_works')
        self.origins.append(replica1)
        self.origins.append(replica2)
        self._default_value = numpy.array([0.0,0.0])
    
    def __repr__(self):

        return 'works {} <> {}: {}'.format(self.origins[0], self.origins[1], 
                                           self.current_value)
