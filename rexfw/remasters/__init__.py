'''
Master classes implementing exchange criteria for RE and derived algorithms
'''

import numpy

from rexfw import Parcel
from rexfw.remasters.requests import SampleRequest, DieRequest, ProposeRequest, AcceptBufferedProposalRequest
from rexfw.remasters.requests import GetStateAndEnergyRequest_master, SendGetStateAndEnergyRequest
from rexfw.remasters.requests import DumpSamplesRequest, SendStatsRequest

from collections import namedtuple
from abc import ABCMeta, abstractmethod


class ExchangeMaster(object):

    def __init__(self, name, replica_names, swap_params, 
                 sampling_statistics, swap_statistics, 
                 comm, swap_list_generator=None):

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
        
    def _send_propose_request(self, r1, r2, params):
        
        request = ProposeRequest(self.name, r2, params)
        self._comm.send(Parcel(self.name, r1, request), dest=r1)

    def _perform_exchanges(self, swap_list):
        
        self._trigger_proposal_calculation(swap_list)
        works, heats = self._receive_works(swap_list)
        acc = self._calculate_acceptance(works)
        self._trigger_exchanges(swap_list, acc)

        return zip(acc, works, heats)

    def _send_get_state_and_energy_request(self, r1, r2):
        
        ## Receives a None from r1 and r2; sent once buffered
        ## state / energies have been set.
        ## This is to sync everything and really hacky
        
        self._comm.send(Parcel(self.name, r2,
                               SendGetStateAndEnergyRequest(self.name, r1)),
                        r2)
        self._comm.recv(source=r2)

    def _trigger_proposal_calculation(self, swap_list):

        for i, (r1, r2, params) in enumerate(swap_list):

            self._send_get_state_and_energy_request(r1, r2)
            self._send_get_state_and_energy_request(r2, r1)
            self._send_propose_request(r1, r2, params)
            params.proposer_params.reverse()
            self._send_propose_request(r2, r1, params)
            params.proposer_params.reverse()
            
    def _receive_works(self, swap_list):

        works = numpy.zeros((len(swap_list), 2))
        heats = numpy.zeros((len(swap_list), 2))
        for i, (r1, r2, params) in enumerate(swap_list):
            data_r1 = self._comm.recv(source=r1).data
            data_r2 = self._comm.recv(source=r2).data
            works[i][0] = data_r1[0]
            works[i][1] = data_r2[0]
            heats[i][0] = data_r1[1]
            heats[i][1] = data_r2[1]
            
        return works, heats

    def _calculate_acceptance(self, works):

        from csb.numeric import exp
        return exp(-numpy.sum(works,1)) > numpy.random.uniform(size=len(works))

    def _trigger_exchanges(self, swap_list, acc):

        for i, (r1, r2, params) in enumerate(swap_list):
            oui = acc[i]
            
            if oui:
                parcel = Parcel(self.name, r1,
                                AcceptBufferedProposalRequest(self.name, True))
                self._comm.send(parcel, r1)
                parcel = Parcel(self.name, r2,
                                AcceptBufferedProposalRequest(self.name, True))
                self._comm.send(parcel, r2)
            else:
                parcel = Parcel(self.name, r1,
                                AcceptBufferedProposalRequest(self.name, False))
                self._comm.send(parcel, r1)
                parcel = Parcel(self.name, r2,
                                AcceptBufferedProposalRequest(self.name, False))
                self._comm.send(parcel, r2)
            self._comm.recv(r1)
            self._comm.recv(r2)

    def _update_swap_stats(self, swap_list, results, step):

        RESwapStats = namedtuple('RESwapStats', 'accepted works heats')
        
        for j, (r1, r2, _) in enumerate(swap_list):
            stats = RESwapStats(results[j][0], results[j][1], results[j][2])
            self.swap_statistics.update([r1, r2], [[self.step, stats]])
                            
    def _calculate_swap_list(self, i):

        return self._swap_list_generator.generate_swap_list(step=i)
        
    def _get_no_ex_replicas(self, swap_list):

        ex_replicas = [[x[0], x[1]] for x in swap_list]
        ex_replicas = [x for z in ex_replicas for x in z]

        return [r for r in self.replica_names if not r in ex_replicas]
        
    def run(self, n_iterations, swap_interval=5, status_interval=100,
            samples_folder=None, dump_interval=250, offset=0, dump_step=5,
            statistics_update_interval=100):

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
                self._send_dump_samples_request(samples_folder,
                                                step - dump_interval,
                                                step, offset, dump_step)

            if step % status_interval == 0 and step > 0:
                self._write_statistics(step)

            if step % statistics_update_interval == 0 and step > 0:
                self._update_sampling_statistics()

            self.step += 1

    def _update_sampling_statistics(self, which_replicas=None):

        if which_replicas is None:
            which_replicas = self.replica_names
            
        for r in which_replicas:
            parcel = Parcel(self.name, r, SendStatsRequest(self.name))
            self._comm.send(parcel, dest=r)

        for r in which_replicas:
            sampler_stats_list = self._comm.recv(source=r).data
            self.sampling_statistics.update(origins=[r],
                                            sampler_stats_list=sampler_stats_list)

    def _write_statistics(self, step):
        
        self.sampling_statistics.write_last(step)
        self.swap_statistics.write_last(step)
            
    def _send_sample_requests(self, targets):

        for t in targets:
            parcel = Parcel(self.name, t, SampleRequest(self.name))
            self._comm.send(parcel, dest=t)

    def _send_dump_samples_request(self, samples_folder, smin, smax, offset,
                                   dump_step):

        for r in self.replica_names:
            request = DumpSamplesRequest(self.name, samples_folder, smin, smax,
                                         offset, dump_step)
            self._comm.send(Parcel(self.name, r, request), dest=r)
        
    def terminate_replicas(self):

        for r in self.replica_names:
            parcel = Parcel(self.name, r, DieRequest(self.name))
            self._comm.send(parcel, dest=r)

