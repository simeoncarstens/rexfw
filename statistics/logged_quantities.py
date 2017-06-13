'''
Logable (?) quantities
'''

from collections import OrderedDict


class LoggedQuantity(object):

    def __init__(self, origins, stats_fields, quantity_name, variable_name=None):

        self._values = OrderedDict()
        self._default_value = None
        self.step = None
        self.origins = origins
        self.stats_fields = stats_fields
        self.quantity_name = quantity_name
        self.variable_name = variable_name

    def __getitem__(self, step):
        return self.values[str(step)] if step != -1 else self.current_value

    @property
    def values(self):
        return self._values

    @property
    def current_value(self):
        return self.values[next(reversed(self.values))] if len(self.values) > 0 else self._default_value

    def _get_value(self, stats):
        pass
    
    def update(self, step, stats):
        self._values.update(**{str(step): self._get_value(stats)})


class SamplerStepsize(LoggedQuantity):

    def __init__(self, replica):

        super(SamplerStepsize, self).__init__([replica], ['stepsize'], 'stepsize')

    def _get_value(self, stats):

        return stats[self.variable_name].stepsize

    def __repr__(self):

        return '{} {} {}: {}'.format(self.origins[0], self.variable_name, 
                                     self.quantity_name,self.current_value)
        

class MCMCMoveAccepted(LoggedQuantity):

    def __init__(self, sampler_name):

        super(MCMCMoveAccepted, self).__init__([sampler_name], ['accepted'], 'accepted')
        self._default_value = None

    def _get_value(self, stats):

        return stats[self.variable_name].accepted

    def __repr__(self):

        return '{} {} {}: {}'.format(self.origins[0], self.variable_name, 
                                     self.quantity_name,self.current_value)


class REMoveAccepted(LoggedQuantity):

    def __init__(self, replica1, replica2):

        super(REMoveAccepted, self).__init__([replica1, replica2], ['accepted'], 'accepted')
        self.__default_value = None

    def _get_value(self, stats):

        return stats.accepted
    
    def __repr__(self):

        return '{} {} {}: {}'.format(self.origins[0], self.variable_name, 
                                     self.quantity_name,self.current_value)


class REWorks(LoggedQuantity):

    def __init__(self, replica1, replica2):

        import numpy 
        
        super(REWorks, self).__init__([replica1, replica2], ['works'], 'works')
        self._default_value = numpy.array([0.0,0.0])

    def _get_value(self, stats):

        return stats.works
    
    def __repr__(self):

        return '{} {} <> {}: {}'.format(self.quantity_name, self.origins[0], self.origins[1], 
                                        self.current_value)

    
class REHeats(LoggedQuantity):

    def __init__(self, replica1, replica2):

        import numpy 
        
        super(REHeats, self).__init__([replica1, replica2], ['heats'], 'heats')
        self._default_value = numpy.array([0.0,0.0])
    
    def _get_value(self, stats):

        return stats.heats

    def __repr__(self):

        return '{} {} <> {}: {}'.format(self.quantity_name, self.origins[0], self.origins[1], 
                                        self.current_value)
