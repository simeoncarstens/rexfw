'''
StatisticsWriter classes which... well... write statistics to stdout / files / ...
'''

import sys

from abc import ABCMeta, abstractmethod


class AbstractStatisticsWriter(object):

    def __init__(self, separator, fields_to_write=None):

        self._separator = separator
        self._fields_to_write = fields_to_write

    def write(self, step, elements, which=None):
        
        if which is None:
            which = self._fields_to_write

        print which
            
        self._write_step_header(step)
        quantity_classes = {quantity_name: elements.select(quantity_name=quantity_name) 
                            for quantity_name in which}
        
        for name, klass in quantity_classes.iteritems():
            sorted_quantities = self._sort_quantities(name, klass)
            self._write_quantity_class_header(name)
            for q in sorted_quantities:
                self._outstream.write(self._format(q) + self._separator)
            self._outstream.write('\n')

class ConsoleStatisticsWriter(AbstractStatisticsWriter):

    __metaclass__ = ABCMeta
    
    def __init__(self, fields_to_write=None):

        super(ConsoleStatisticsWriter, self).__init__(' ', fields_to_write)
        self._outstream = sys.stdout
        
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
    

class StandardConsoleMCMCStatisticsWriter(ConsoleStatisticsWriter):
    '''
    Only prints acceptance rate and stepsize
    '''

    def __init__(self):

        # super(StandardConsoleMCMCStatisticsWriter, self).__init__(['mcmc_p_acc', 'stepsize'])
        super(StandardConsoleMCMCStatisticsWriter, self).__init__([])
    
    def _format(self, quantity):

        if quantity.name == 'mcmc_p_acc':
            return '{: >.3f}   '.format(quantity.current_value)
        if quantity.name == 'stepsize':
            return '{: <.2e}'.format(quantity.current_value)
    
    def _write_step_header(self, step):

        self._outstream.write('######### MC step: {} #########\n'.format(step))

    def _sort_quantities(self, name, quantity_class):

        return sorted(quantity_class, key=lambda x: int(list(x.origins)[0][len('sampler_replica'):]))
    
    def _write_quantity_class_header(self, class_name):

        if class_name == 'mcmc_p_acc':
            self._outstream.write('MCMC    p_acc: ')
        if class_name == 'stepsize':
            self._outstream.write('MCMC stepsize: ')

            
class StandardConsoleREStatisticsWriter(ConsoleStatisticsWriter):

    def __init__(self):

        super(StandardConsoleREStatisticsWriter, self).__init__(['RE acceptance rate'])

    def _format(self, quantity):

        if quantity.quantity_name == 'RE acceptance rate':
            return '{: >.2f}   '.format(quantity.current_value)

    def _write_quantity_class_header(self, class_name):

        self._outstream.write('RE      p_acc: ')

    def _sort_quantities(self, name, quantity_class):

        return sorted(quantity_class, key=lambda x: min([int(y[len('replica'):]) 
                                                         for y in x.origins]))

    def _write_step_header(self, step):
        pass
 
        
class AbstractFileStatisticsWriter(AbstractStatisticsWriter):

    __metaclass__ = ABCMeta
    
    def __init__(self, filename, fields_to_write=None):

        super(AbstractFileStatisticsWriter, self).__init__('\t', fields_to_write)
        
        self._filename = filename
        self._outstream = open(filename, 'w')
        self._write_header()
        self._outstream.close()
        self._separator = '\t'

    def write(self, step, elements, fields=None):

        self._outstream = open(self._filename, 'a')
        super(AbstractFileStatisticsWriter, self).write(step, elements, fields)
        self._outstream.close()
        
    @abstractmethod
    def _write_quantity_class_header(self, class_name):
        pass

class StandardFileMCMCStatisticsWriter(AbstractFileStatisticsWriter):

    def __init__(self, filename, fields_to_write=None):
        
        super(StandardFileMCMCStatisticsWriter, self).__init__(filename, fields_to_write)

        self._separator = '\t'
        self._fields_to_write = ['mcmc_p_acc', 'stepsize']
    
    def _format(self, quantity):

        return str(quantity.current_value)

    def _write_header(self):

        # self._outstream.write('{} '.format(step))
        pass

    def _write_step_header(self, step):

        self._outstream.write('{}\t'.format(step))

    def _sort_quantities(self, name, quantity_class):

        return sorted(quantity_class, key=lambda x: int(list(x.origins)[0][len('sampler_replica'):]))

    def _write_quantity_class_header(self, class_name):
        pass


class StandardFileREStatisticsWriter(AbstractFileStatisticsWriter):

    def __init__(self, filename, fields_to_write=None):
        
        fields_to_write = ['RE acceptance rate'] if fields_to_write is None else fields_to_write
        
        super(StandardFileREStatisticsWriter, self).__init__(filename, fields_to_write)

        self._separator = '\t'
    
    def _format(self, quantity):

        return str(quantity.current_value)

    def _write_header(self):

        # self._outstream.write('{} '.format(step))
        pass

    def _write_step_header(self, step):

        self._outstream.write('{}\t'.format(step))

    def _sort_quantities(self, name, quantity_class):

        return sorted(quantity_class, key=lambda x: min([int(y[len('replica'):]) 
                                                         for y in x.origins]))

    def _write_quantity_class_header(self, class_name):
        pass


class StandardFileREWorksStatisticsWriter(object):

    def __init__(self, outfolder):

        self._outfolder = outfolder
        self._fields_to_write = ['re_works']

    def write(self, elements):

        from cPickle import dump
        
        for e in elements:
            with open(self._outfolder + 'works_{}-{}.pickle'.format(*e.origins), 'w') as opf:
                dump(e.values, opf)


class StandardFileREHeatsStatisticsWriter(object):

    def __init__(self, outfolder):

        self._outfolder = outfolder
        self._fields_to_write = ['re_heats']

    def write(self, elements):

        from cPickle import dump
        
        for e in elements:
            with open(self._outfolder + 'heats_{}-{}.pickle'.format(*e.origins), 'w') as opf:
                dump(e.values, opf)
