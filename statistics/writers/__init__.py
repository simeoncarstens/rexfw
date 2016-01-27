'''
StatisticsWriter classes which... well... write statistics to stdout / files / ...
'''

import sys

from abc import ABCMeta, abstractmethod

alphansort = lambda data: sorted(data, key=lambda item: (int(item.partition(' ')[0])
                                                         if item[0].isdigit() else float('inf'), item))

class AbstractStatisticsWriter(object):

    _outstream = None

    @abstractmethod
    def write(self, step, elements, fields=None):

        pass


class ConsoleStatisticsWriter(AbstractStatisticsWriter):

    def __init__(self, fields_to_write=None):

        self._fields_to_write = fields_to_write

    _outstream = sys.stdout

    # def write(self, step, elements, fields=None):
    #     '''
    #     Sorts keys by default alphanumerically
    #     '''
    #     for x in elements:
    #         if fields is None:
    #             temp_fields = x.keys()
    #         else:
    #             temp_fields = [k for k in x.keys() if k in fields]
    #         self._write_header(step, elements, fields)
    #         ## HACK
    #         sorted_fields = self._sort_fields(temp_fields)
    #         for k in sorted_fields:
    #             self._outstream.write(self._format(k, x[k]) + ' ')
    #         self._outstream.write('\n')

    def write(self, step, elements, which=None):
        '''
        Sorts keys by default alphanumerically
        '''

        if which is None:
            which = self._fields_to_write

        for x in elements:
            self._write_step_header(step)
            quantity_classes = {name: x.select(name=name) for name in which}
            for name, klass in quantity_classes.iteritems():
                sorted_quantities = self._sort_quantities(name, klass)
                self._write_quantity_class_header(name)
                for q in sorted_quantities:    
                    self._outstream.write(self._format(q) + ' ')
                self._outstream.write('\n')
        
    @abstractmethod
    def _format(self, quantity):
        pass

    @abstractmethod
    def _sort_quantities(self, name, klass):
        pass
    
    @abstractmethod
    def _write_step_header(self, step):
        pass

    @abstractmethod
    def _write_quantity_class_header(self, class_name):
        pass
    

class SimpleConsoleMCMCStatisticsWriter(ConsoleStatisticsWriter):
    '''
    Only prints acceptance rate and stepsize
    '''

    def __init__(self):

        super(SimpleConsoleMCMCStatisticsWriter, self).__init__(['p_acc', 'stepsize'])
    
    def _format(self, quantity):

        return '{:.2f}'.format(quantity.value)

    def _write_step_header(self, step):

        self._outstream.write('######### MC step: {}#########\n'.format(step))

    def _sort_quantities(self, name, quantity_class):

        return sorted(quantity_class, key=lambda x: int(x.sampler_name[len('sampler_replica'):]))
    
    @abstractmethod
    def _write_quantity_class_header(self, class_name):
        if class_name == 'p_acc':
            self._outstream.write('MCMC p_acc: ')
        if class_name == 'stepsize':
            self._outstream.write('MCMC stpsze: ')

    
class SimpleConsoleREStatisticsWriter(ConsoleStatisticsWriter):

    def _format(self, quantity):

        if quantity.name == 're_p_acc':
            return '{:.2f}'.format(quantity.value)

    def _write_quantity_class_header(self, class_name):

        self._outstream.write('RE p_acc:   ')

    def _sort_quantities(self, name, quantity_class):

        return sorted(quantity_class, key=lambda x: min([int(y[len('replica'):]) 
                                                         for y in x.origins]))
 
        
# class AbstractSimpleFileStatisticsWriter(AbstractStatisticsWriter):

#     def __init__(self, filename):

#         self._filename = filename
#         self._outstream = file(filename, 'a')
#         self._outstream.close()

#     def write(self, step, elements, fields=None):

#         self._outstream.open()
#         super(SimpleFileStatisticsWriter, self).write(step, elements, fields)
#         self._outstream.close()
        

# class SimpleFileMCMCStatisticsWriter(AbstractStatisticsWriter):

#     def _format(self, field_name, data):

#         return float(data['p_acc'].__repr__())

#     def _write_header(self, step, elements, fields):

#         self._outstream.write('{} '.format(step))
