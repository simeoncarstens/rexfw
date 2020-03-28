'''
StatisticsWriter classes which... well... write statistics to stdout / files / ...

ATTENTION: some of these classes expect replica objects to be named replica1, replica2, ...
'''

import sys

from abc import abstractmethod


class AbstractStatisticsWriter(object):

    def __init__(self, separator, variables_to_write=[], quantities_to_write=[]):
        '''
        Base class for classes which write sampling statistics to stdout, files, ...

        :param str separator: separator string separating values of different
                              quantities in written output

        :param variables_to_write: list of sampling variable names for which to
                                   write statistics
        :type variables_to_write: list of str

        :param quantities_to_write: list of :class:`.LoggedQuantity` objects for which to
                                    write statistics
        :type quantities_to_write: list of :class:`.LoggedQuantity`
        '''
        self._separator = separator
        self.variables_to_write = variables_to_write
        self.quantities_to_write = quantities_to_write

    @abstractmethod
    def write(self, step, elements):
        '''
        Writes quantities in elements for a given step

        :param int step: sampling step
        :param elements: list of quantities to write
        :type elements: list of :class:`.LoggedQuantity`
        '''
        pass
    
    def _write_single_quantity_stats(self, elements):
        '''
        Writes a single line to stdout / file, e.g., all sampler step sizes
        which would be stored in elements

        :param elements: quantities to write
        :type elements: list of :class:`.LoggedQuantity`
        '''
        self._write_quantity_class_header(elements[0])
        for e in self._sort_quantities(elements):
            self._outstream.write(self._format(e) + self._separator)
        self._outstream.write('\n')
           

class ConsoleStatisticsWriter(AbstractStatisticsWriter):

    def __init__(self, variables_to_write=[], quantities_to_write=[]):
        '''
        Writes sampling statistics to stdout

        :param variables_to_write: list of sampling variable names for which to
                                   write statistics
        :type variables_to_write: list of str

        :param quantities_to_write: list of :class:`.LoggedQuantity` objects for which to
                                    write statistics
        :type quantities_to_write: list of :class:`.LoggedQuantity`
        '''

        super(ConsoleStatisticsWriter, self).__init__(' ', variables_to_write,
                                                      quantities_to_write)
        self._outstream = sys.stdout
        
    @abstractmethod
    def _format(self, quantity):
        '''
        Formats the numeric value of a quantity for output

        :param quantity: a quantity whose numeric value will be written
        :type quantity: :class:`.LoggedQuantity`

        :return: a string representing a formatted numerical value
        :rtype: str
        '''
        pass

    @abstractmethod
    def _sort_quantities(self, quantities):
        '''
        Sorts quantities for a single line by, e.g., replica name

        :param quantities: the logged quantitis which will be written out
        :type quantities: list of :class:`.LoggedQuantity` objects

        :return: the sorted quantities list
        :rtype: list
        '''
        pass
    
    @abstractmethod
    def _write_step_header(self, step):
        '''
        Writes a header for a given sampling step, e.g., ### step number ###

        :param int step: a sampling step

        :return: the header prefacing the ouptut for a given sampling step
        :rtype: str
        '''
        pass

    @abstractmethod
    def _write_quantity_class_header(self, quantity):
        '''
        Writes a "header" (line beginning) for a given type of quantity,
        e.g., "myvariable p_acc"

        :param quantity: a quantity containing the information needed
        :type quantity: :class:`.LoggedQuantity`

        :return: a preface for a line with similar sampling statistics
        :rtype: str
        '''
        pass

    def _write_all_but_header(self, quantities):
        '''
        Writes all sampling statistics in quantities, but not the line header

        :param quantities: a list of similar :class:`.LoggedQuantity` objects, e.g.,
                           all step sizes
        :type quantities: list of :class:`.LoggedQuantity`
        '''

        for quantity_name in list(set([quantity.name for quantity in quantities])):
            quantities2 = quantities.select(name=quantity_name)
            self._write_single_quantity_stats(quantities2)

    def write(self, step, elements):

        self._write_step_header(step)
        self._write_all_but_header(elements)
        

class StandardConsoleMCMCStatisticsWriter(ConsoleStatisticsWriter):
    '''
    Writes only acceptance rate and step sizes to stdout.
    Remember to set quantity names correctly, that is, to
    "acceptance rate" and "stepsize"

    :param variables_to_write: list of sampling variable names for which to
                               write statistics
    :type variables_to_write: list of str

    :param quantities_to_write: list of :class:`.LoggedQuantity` objects for which to
                                write statistics
    :type quantities_to_write: list of :class:`.LoggedQuantity`
    '''

    def _format(self, quantity):
        
        if 'acceptance rate' in quantity.name:
            return '{: >.3f}   '.format(quantity.current_value)
        elif 'stepsize' in quantity.name:
            if quantity.current_value is None:
                return 'n/a'.format(quantity.current_value)
            else:
                return '{: >.2e}'.format(quantity.current_value)
    
    def _write_step_header(self, step):

        self._outstream.write('######### MC step: {} #########\n'.format(step))

    def _sort_quantities(self, quantities):

        return sorted(quantities,
                      key=lambda x: int(list(x.origins)[0][len('replica'):]))
    
    def _write_quantity_class_header(self, quantity):
        
        self._outstream.write('{:<10} {:>16}: '.format(quantity.variable_name,
                                                       quantity.name))

    def _write_all_but_header(self, elements):

        for variable_name in self.variables_to_write:
            quantities = elements.select(variable_name=variable_name)
            super(StandardConsoleMCMCStatisticsWriter, self)._write_all_but_header(quantities)
            
            
class StandardConsoleREStatisticsWriter(ConsoleStatisticsWriter):

    def __init__(self):
        '''
        Writes replica exchange acceptance rates to stdout.
        Remember to set quantity names correctly, that is, to
        "acceptance rate"
        '''

        super(StandardConsoleREStatisticsWriter, self).__init__(quantities_to_write=['acceptance rate'])

    def _format(self, quantity):

        if quantity.name == 'acceptance rate':
            return '{: >.3f}   '.format(quantity.current_value)

    def _write_quantity_class_header(self, class_name):

        self._outstream.write('{:<10} {:>16}: '.format('RE', 'acceptance rate'))

    def _sort_quantities(self, quantities):

        return sorted(quantities, key=lambda x: min([int(y[len('replica'):]) 
                                                for y in x.origins]))
    
    def _write_step_header(self, step):
        pass
 
        
class AbstractFileStatisticsWriter(AbstractStatisticsWriter):

    def __init__(self, filename, variables_to_write=[], quantities_to_write=[]):
        '''
        Writes sampling statistics to a file.

        :param str filename: path to file to write sampling statistics to

        :param variables_to_write: list of sampling variable names for which to
                                   write statistics
        :type variables_to_write: list of str

        :param quantities_to_write: list of :class:`.LoggedQuantity` objects for which to
                                    write statistics
        :type quantities_to_write: list of :class:`.LoggedQuantity`
        '''

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
        '''
        Writes acceptance rates and step sizes to a file.        

        :param str filename: path to file to write sampling statistics to

        :param variables_to_write: list of sampling variable names for which to
                                   write statistics
        :type variables_to_write: list of str

        :param quantities_to_write: list of :class:`.LoggedQuantity` objects for which to
                                    write statistics
        :type quantities_to_write: list of :class:`.LoggedQuantity`
        '''
        
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
    '''
    Writes replica exchange acceptance rates to a file.

    :param str filename: path to file to write sampling statistics to

    :param variables_to_write: list of sampling variable names for which to
                               write statistics
    :type variables_to_write: list of str

    :param quantities_to_write: list of :class:`.LoggedQuantity` objects for which to
                                write statistics
    :type quantities_to_write: list of :class:`.LoggedQuantity`
    '''

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


class StandardFileREWorksStatisticsWriter(AbstractStatisticsWriter):

    def __init__(self, outfolder):
        '''
        Writes works expended during replica exchange swap trajectories to a file.        

        :param str outfolder: path to folder to write works to
        '''

        self._outfolder = outfolder
        self._quantities_to_write = ['re_works']

    def write(self, elements):

        from pickle import dump
        
        for e in elements:
            with open(self._outfolder + 'works_{}-{}.pickle'.format(*e.origins), 'w') as opf:
                dump(e.values, opf)


class StandardFileREHeatsStatisticsWriter(AbstractStatisticsWriter):
    '''
    Writes heats produced during replica exchange swap trajectories to a file.        

    :param str outfolder: path to folder to write heats to
    '''

    def __init__(self, outfolder):

        self._outfolder = outfolder
        self._quantities_to_write = ['re_heats']

    def write(self, elements):

        from pickle import dump
        
        for e in elements:
            with open(self._outfolder + 'heats_{}-{}.pickle'.format(*e.origins), 'w') as opf:
                dump(e.values, opf)
