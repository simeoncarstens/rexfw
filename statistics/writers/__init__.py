'''
StatisticsWriter classes which... well... write statistics to stdout / files / ...
'''

import sys

from abc import ABCMeta, abstractmethod


class AbstractStatisticsWriter(object):

    def __init__(self, separator, variables_to_write=[], quantities_to_write=[]):

        self._separator = separator
        self.variables_to_write = variables_to_write
        self.quantities_to_write = quantities_to_write

    @abstractmethod
    def write(self, step, elements):
        pass
    
    def _write_single_quantity_stats(self, elements):

        self._write_quantity_class_header(elements[0])
        for e in self._sort_quantities(elements):
            self._outstream.write(self._format(e) + self._separator)
        self._outstream.write('\n')
           

class ConsoleStatisticsWriter(AbstractStatisticsWriter):

    __metaclass__ = ABCMeta
    
    def __init__(self, variables_to_write=[], quantities_to_write=[]):

        super(ConsoleStatisticsWriter, self).__init__(' ', variables_to_write,
                                                      quantities_to_write)
        self._outstream = sys.stdout
        
    @abstractmethod
    def _format(self, quantity):
        pass

    @abstractmethod
    def _sort_quantities(self, quantities):
        pass
    
    @abstractmethod
    def _write_step_header(self, step):
        pass

    @abstractmethod
    def _write_quantity_class_header(self, class_name):
        pass

    def _write_all_but_header(self, quantities):

        for quantity_name in list(set([quantity.name for quantity in quantities])):
            quantities2 = quantities.select(name=quantity_name)
            self._write_single_quantity_stats(quantities2)

    def write(self, step, elements):

        self._write_step_header(step)
        self._write_all_but_header(elements)
        

class StandardConsoleMCMCStatisticsWriter(ConsoleStatisticsWriter):
    '''
    Only prints acceptance rate and stepsize
    '''

    def _format(self, quantity):
        
        if 'acceptance rate' in quantity.name:
            return '{: >.3f}   '.format(quantity.current_value)
        elif 'stepsize' in quantity.name:
            return '{: <.2e}'.format(quantity.current_value)
    
    def _write_step_header(self, step):

        self._outstream.write('######### MC step: {} #########\n'.format(step))

    def _sort_quantities(self, quantities):

        return sorted(quantities,
                      key=lambda x: int(list(x.origins)[0][len('replica'):]))
    
    def _write_quantity_class_header(self, quantity):
        
        self._outstream.write('{:>10} {:>16}: '.format(quantity.variable_name,
                                                       quantity.name))

    def _write_all_but_header(self, elements):

        for variable_name in self.variables_to_write:
            quantities = elements.select(variable_name=variable_name)
            super(StandardConsoleMCMCStatisticsWriter, self)._write_all_but_header(quantities)
            
            
class StandardConsoleREStatisticsWriter(ConsoleStatisticsWriter):

    def __init__(self):

        super(StandardConsoleREStatisticsWriter, self).__init__(quantities_to_write=['acceptance rate'])

    def _format(self, quantity):

        if quantity.name == 'acceptance rate':
            return '{: >.3f}   '.format(quantity.current_value)

    def _write_quantity_class_header(self, class_name):

        self._outstream.write('{:>10} {:>16}: '.format('RE', 'acceptance rate'))

    def _sort_quantities(self, quantities):

        return sorted(quantities, key=lambda x: min([int(y[len('replica'):]) 
                                                for y in x.origins]))
    
    def _write_step_header(self, step):
        pass
 
        
class AbstractFileStatisticsWriter(AbstractStatisticsWriter):

    __metaclass__ = ABCMeta
    
    def __init__(self, filename, variables_to_write=[], quantities_to_write=[]):

        super(AbstractFileStatisticsWriter, self).__init__('\t',
                                                           variables_to_write,
                                                           quantities_to_write)
        
        self._filename = filename
        self._outstream = open(filename, 'w')
        self._write_header()
        self._outstream.close()
        self._separator = '\t'

    @abstractmethod
    def write(self, step, elements):

        self._outstream = open(self._filename, 'a')
        ## fill in here in subclasses
        self._outstream.close()
        
    @abstractmethod
    def _write_quantity_class_header(self, class_name):
        pass

class StandardFileMCMCStatisticsWriter(AbstractFileStatisticsWriter):

    def __init__(self, filename, variables_to_write=[], quantities_to_write=[]):
        
        super(StandardFileMCMCStatisticsWriter, self).__init__(filename,
                                                               variables_to_write,
                                                               quantities_to_write)

        self._separator = '\t'
    
    def _format(self, quantity):

        return str(quantity.current_value)

    def _write_header(self):

        pass

    def _write_step_header(self, step):

        self._outstream.write('{}\t'.format(step))

    def _sort_quantities(self, quantities):

        return sorted(quantities, key=lambda x: int(list(x.origins)[0][len('replica'):]))

    def _write_quantity_class_header(self, quantity):
        pass

    def _write_all_but_header(self, quantities):

        self._write_single_quantity_stats(quantities)

    def write(self, step, elements):

        self._outstream = open(self._filename, 'a')
        self._write_step_header(step)
        self._write_all_but_header(elements)
        self._outstream.close()
        

class StandardFileREStatisticsWriter(AbstractFileStatisticsWriter):

    def __init__(self, filename, quantities_to_write=[]):
                
        super(StandardFileREStatisticsWriter, self).__init__(filename,
                                                             [],
                                                             quantities_to_write)

        self._separator = '\t'
    
    def _format(self, quantity):

        return str(quantity.current_value)

    def _write_header(self):

        pass

    def _write_step_header(self, step):

        self._outstream.write('{}\t'.format(step))

    def _sort_quantities(self, quantities):

        return sorted(quantities, key=lambda x: min([int(y[len('replica'):]) 
                                                     for y in x.origins]))

    def _write_quantity_class_header(self, class_name):
        pass

    def write(self, step, elements):

        self._outstream = open(self._filename, 'a')
        self._write_step_header(step)
        self._write_all_but_header(elements)
        self._outstream.close()

    def _write_all_but_header(self, quantities):

        self._write_single_quantity_stats(quantities)


class StandardFileREWorksStatisticsWriter(object):

    def __init__(self, outfolder):

        self._outfolder = outfolder
        self._quantities_to_write = ['re_works']

    def write(self, elements):

        from cPickle import dump
        
        for e in elements:
            with open(self._outfolder + 'works_{}-{}.pickle'.format(*e.origins), 'w') as opf:
                dump(e.values, opf)


class StandardFileREHeatsStatisticsWriter(object):

    def __init__(self, outfolder):

        self._outfolder = outfolder
        self._quantities_to_write = ['re_heats']

    def write(self, elements):

        from cPickle import dump
        
        for e in elements:
            with open(self._outfolder + 'heats_{}-{}.pickle'.format(*e.origins), 'w') as opf:
                dump(e.values, opf)
