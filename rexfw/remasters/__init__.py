'''
Master classes implementing exchange criteria for RE and derived algorithms
'''

import numpy as np

from rexfw import Parcel
from rexfw.remasters.requests import SampleRequest, DieRequest, ProposeRequest, AcceptBufferedProposalRequest
from rexfw.remasters.requests import GetStateAndEnergyRequest_master, SendGetStateAndEnergyRequest
from rexfw.remasters.requests import DumpSamplesRequest, SendStatsRequest

from abc import ABCMeta, abstractmethod


class ExchangeMaster(object):

    def __init__(self, name, replica_names, swap_params, 
                 sampling_statistics, swap_statistics, 
                 comm, swap_list_generator=None):
        '''
        Default master object to coordinate RE(NS) swaps

        :param name: a name for the object. TODO: atm, has to be 'master0' for the
                     MPICommunicator to work
        :type name: String

        :param replica_names: a list containing the names of all the replicas
        :type replica_names: list

        :param swap_params: a list of :class:`.ExchangeParams` objects
        :type swap_params: list

        :param sampling_statistics: a :class:`.Statistics` object to log sampling statistics like
                                    acceptance rates etc.
        :type sampling_statistics: :class:`.Statistics`

        :param swap_statistics: a :class:`.REStatistics` object to log replica exchange statistics
                                like acceptance rates etc.
        :type swap_statistics: :class:`.REStatistics`

        :param comm: a communicator object in charge of communicating with the replicas
        :type comm: AbstractCommunicator

        :param swap_list_generator: an object which creates swap lists with items
                                    consisting of two replica names and a parameter object            
        :type swap_list_generator: :class:`.AbstractSwapListGenerator`
        '''
        self.name = name
        self.replica_names = replica_names
        self._n_replicas = len(self.replica_names)
        self._swap_params = swap_params
        self.sampling_statistics = sampling_statistics
        self.swap_statistics = swap_statistics
        self._comm = comm
        if swap_list_generator is None:
            from rexfw.slgenerators import StandardSwapListGenerator
            swap_list_generator = StandardSwapListGenerator(self._n_replicas,
                                                            self._swap_params)
        self._swap_list_generator = swap_list_generator
        self.step = 0
        
    def _send_propose_request(self, replica1, replica2, params):
        '''
        Sends a request to replica1 telling it to propose a state for replica2
        using information in params (an ExchangeParams object defined in )

        :param replica1: name of 1st replica involved in swap
        :type replica1: String

        :param replica2: name of 2nd replica involved in swap
        :type replica2: String

        :param params: an :class:`.ExchangeParams` object holding information required
                       to perform the swap
        :type params: :class:`.ExchangeParams`
        '''
        
        request = ProposeRequest(self.name, replica2, params)
        self._comm.send(Parcel(self.name, replica1, request), dest=replica1)

    def _perform_exchanges(self, swap_list):
        '''
        Attempts exchanges defined in swap_list. 

        :param swap_list: a list of list in which each list element contains two replica  
                          names involved in a swap an an :class:`.ExchangeParams` object
        :type swap_list: list

        :return: three lists: acceptance statuses (0 / 1), works  and heats
        :rtype: list
        '''
        
        self._trigger_proposal_calculation(swap_list)
        works, heats = self._receive_works(swap_list)
        acc = self._calculate_acceptance(works)
        self._trigger_exchanges(swap_list, acc)

        return zip(acc, works, heats)

    def _send_get_state_and_energy_request(self, replica1, replica2):
        '''
        Sends a request to replica1 to make it send a request to replica2 ordering
        it (replica2) to send its (replica2) state and and energy to replica1. 
        Receives a None from replica1 and replica2; sent once buffered
        state / energies have been set.
        This is to sync everything and really hacky

        :param replica1: name of 1st replica involved in swap
        :type replica1: String

        :param replica2: name of 2nd replica involved in swap
        :type replica2: String
        '''
        self._comm.send(Parcel(self.name, replica2,
                               SendGetStateAndEnergyRequest(self.name, replica1)),
                        replica2)
        self._comm.recv(source=replica2)

    def _trigger_proposal_calculation(self, swap_list):
        '''
        Makes all involved replicas propose states.

        :param swap_list: a list of list in which each list element contains two replica  
                          names involved in a swap an an :class:`.ExchangeParams` object
        :type swap_list: list
        '''

        for i, (replica1, replica2, params) in enumerate(swap_list):

            self._send_get_state_and_energy_request(replica1, replica2)
            self._send_get_state_and_energy_request(replica2, replica1)
            self._send_propose_request(replica1, replica2, params)
            params.proposer_params.reverse()
            self._send_propose_request(replica2, replica1, params)
            params.proposer_params.reverse()
            
    def _receive_works(self, swap_list):
        '''
        Receives works from all swapping replicas.
        
        :param swap_list: a list of list in which each list element contains two replica  
                          names involved in a swap an an :class:`.ExchangeParams` object
        :type swap_list: list

        :return: lists of works and heats
        :rtype: list
        '''

        works = np.zeros((len(swap_list), 2))
        heats = np.zeros((len(swap_list), 2))
        for i, (replica1, replica2, params) in enumerate(swap_list):
            data_replica1 = self._comm.recv(source=replica1).data
            data_replica2 = self._comm.recv(source=replica2).data
            works[i][0] = data_replica1[0]
            works[i][1] = data_replica2[0]
            heats[i][0] = data_replica1[1]
            heats[i][1] = data_replica2[1]
            
        return works, heats

    def _calculate_acceptance(self, works):
        '''
        Determines whether swaps are being accepted or rejected

        :param works: array of works with shape (number of swaps, 2),
                      the 2nd dimension are the works for forward- and backward
                      trajectory
        :type works: numpy.ndarray

        :return: array of Boolean (0 / 1) values indicating whether swaps have
                 been accepted (1) or rejected (0)              
        :rtype: numpy.ndarray
        '''

        return np.exp(-np.sum(works,1)) > np.random.uniform(size=len(works))

    def _send_accept_exchange_request(self, dest):
        '''
        Sends a request to accept a proposed swap state.

        :param dest: name of destination replica
        :type dest: String
        '''
        parcel = Parcel(self.name, dest,
                        AcceptBufferedProposalRequest(self.name, True))
        self._comm.send(parcel, dest)

    def _send_reject_exchange_request(self, dest):
        '''
        Sends a request to reject a proposed swap state.

        :param dest: name of destination replica
        :type dest: String
        '''
        parcel = Parcel(self.name, dest,
                        AcceptBufferedProposalRequest(self.name, False))
        self._comm.send(parcel, dest)
        
    def _trigger_exchanges(self, swap_list, acc):
        '''
        Sends accept / reject exchange requests to all involved replicas

        :param swap_list: a list of list in which each list element contains two replica  
                          names involved in a swap an an :class:`.ExchangeParams` object
        :type swap_list: list

        :param acc: array containing boolean (0 / 1) values indicating which
                    swaps have been accepted and which haven't
        :type acc: numpy.ndarray
        '''
        for i, (replica1, replica2, params) in enumerate(swap_list):
            accept_exchange = acc[i]
            
            if accept_exchange:
                self._send_accept_exchange_request(replica1)
                self._send_accept_exchange_request(replica2)
            else:
                self._send_reject_exchange_request(replica1)
                self._send_reject_exchange_request(replica2)
            ## receives DoNothingRequests to achieve synchronisation
            self._comm.recv(replica1)
            self._comm.recv(replica2)

    def _update_swap_stats(self, swap_list, results, step):
        '''
        Updates replica exchange statistics.

        :param swap_list: a list of list in which each list element contains two replica  
                          names involved in a swap an an :class:`.ExchangeParams` object
        :type swap_list: list

        :param results: a two-dimensional list of shape (number of swaps, 3), in which
                        the 2nd dimension is (0 / 1 (reject / accept), works, heats)
        :type results: list

        :param step: the sampling step at which the swaps were performed
        :type step: int
        '''

        ## TODO: this shouldn't be here...
        from collections import namedtuple
        RESwapStats = namedtuple('RESwapStats', 'accepted works heats')
        
        for j, (replica1, replica2, _) in enumerate(swap_list):
            stats = RESwapStats(results[j][0], results[j][1], results[j][2])
            self.swap_statistics.update([replica1, replica2], [[self.step, stats]])
                            
    def _calculate_swap_list(self, step):
        '''
        Creates the swap list for a given step

        :param step: the sampling step for which to create the swap list
        :type step: int

        :return: a list of list in which each list element contains two replica  
                 names involved in a swap an an :class:`.ExchangeParams` object
        :rtype: list
        '''

        return self._swap_list_generator.generate_swap_list(step=step)
        
    def _get_no_ex_replicas(self, swap_list):
        '''
        For a given swap list, calculate which replicas do NOT perform swaps
        and thus will continue normal sampling.

        :param swap_list: a list of list in which each list element contains two replica  
                          names involved in a swap an an :class:`.ExchangeParams` object
        :type swap_list: list

        :return: a list of replica names
        :rtype: list
        '''

        ex_replicas = [[x[0], x[1]] for x in swap_list]
        ex_replicas = [x for z in ex_replicas for x in z]

        return [replica_name for replica_name in self.replica_names 
                if not replica_name in ex_replicas]
        
    def run(self, n_iterations, swap_interval=5, status_interval=100,
            dump_interval=250, offset=0, dump_step=5,
            statistics_update_interval=100):
        '''
        Runs the main loop of length n_iterations (number of sampling steps),
        in which normal sampling and swaps are performed.
        Furthermore, in given intervals, statistics are updated and statistics
        and samples are written to files.

        :param n_iterations: number of sampling steps to perform
        :type n_iterations: int

        :param swap_interval: the interval with which to perform swaps
        :type swap_interval: int

        :param status_interval: the interval with which to write sampling statistics
        :type status_interval: int

        :param dump_interval: the interval with which to write samples to files
        :type dump_interval: int

        :param offset: an offset to add to the sample counter when writing samples
                       to files. This allows to continue simulations.
        :type offset: int

        :param dump_step: allows to perform sub-sampling: write only every dump_step-th
                          sample to a file
        :type dump_step: int

        :param statistics_update_interval: interval with which to update sampling
                                           statistics
        :type statistics_update_interval: int
        '''

        for step in xrange(n_iterations):
            if step % swap_interval == 0 and step > 0:
                swap_list = self._calculate_swap_list(step)
                results = self._perform_exchanges(swap_list)
                self._update_swap_stats(swap_list, results, step)
                no_ex_replicas = self._get_no_ex_replicas(swap_list)
                self._send_sample_requests(no_ex_replicas)
            else:
                self._send_sample_requests(self.replica_names)
                
            if step % dump_interval == 0 and step > 0:
                self._send_dump_samples_request(step - dump_interval,
                                                step, offset, dump_step)

            if step % status_interval == 0 and step > 0:
                self._write_statistics(step)

            if step % statistics_update_interval == 0 and step > 0:
                self._update_sampling_statistics()

            self.step += 1

    def _send_send_stats_requests(self, replicas):
        '''
        Send requests to replicas to send sampling statistics to this master object.

        :param replica: replica names
        :type replicas: list
        '''

        for r in replicas:
            parcel = Parcel(self.name, r, SendStatsRequest(self.name))
            self._comm.send(parcel, dest=r)

    def _receive_and_update_stats(self, replicas):
        '''
        Receive sampling statistics from replicas and update statistics object

        :param replicas: replica names
        :type replicas: list
        '''

        for r in replicas:
            sampler_stats_list = self._comm.recv(source=r).data
            self.sampling_statistics.update(origins=[r],
                                            sampler_stats_list=sampler_stats_list)

    def _update_sampling_statistics(self, which_replicas=None):
        '''
        Update sampling statistics

        :params which_replicas: replicas for which to update statistics
        :type which_replicas: list
        '''
        
        if which_replicas is None:
            which_replicas = self.replica_names

        self._send_send_stats_requests(which_replicas)
        self._receive_and_update_stats(which_replicas)
        
    def _write_statistics(self, step):
        '''
        Write sampling and swap statistics

        :param step: sampling step
        :type step: int
        '''
        
        self.sampling_statistics.write_last(step)
        self.swap_statistics.write_last(step)
            
    def _send_sample_requests(self, replicas):
        '''
        Send requests to replicas to sample from their respective PDFs

        :param replicas: replicas which are supposed to perform a sampling step
        :type replicas: list  
        '''

        for replica_name in replicas:
            parcel = Parcel(self.name, replica_name, SampleRequest(self.name))
            self._comm.send(parcel, dest=replica_name)

    def _send_dump_samples_request(self, smin, smax, offset, dump_step):
        '''
        Send requests to write samples to files

        :param smin: first sample index
        :type smin: int

        :param smax: last sample index
        :type smax: int

        :param offset: offset which to add to sample index
        :type offset: int

        :param dump_step: sub-sampling step; write only every dump_step-th sample
        :type dump_step: int
        '''

        for r in self.replica_names:
            request = DumpSamplesRequest(self.name, smin, smax, offset, dump_step)
            self._comm.send(Parcel(self.name, r, request), dest=r)
        
    def terminate_replicas(self):
        '''
        Makes all replicas break from their listening loop and quit
        '''

        for r in self.replica_names:
            parcel = Parcel(self.name, r, DieRequest(self.name))
            self._comm.send(parcel, dest=r)

