'''
Master classes implementing exchange criteria for RE and derived algorithms
'''

from rexfw import Parcel
from rexfw.remasters.requests import SampleRequest, DieRequest


class ReplicaExchangeMaster(object):

    # __metaclass__ = ABCMeta
    
    def __init__(self, name, n_replicas, comm, sampling_statistics=None, swap_statistics=None, id_offset=1):

        self.name = name
        self._n_replicas = n_replicas
        self.sampling_statistics = sampling_statistics
        self.swap_statistics = swap_statistics
        self._comm = comm
        self.id_offset = id_offset
        self.step = 0

    # def _perform_exchanges(self, swap_list):

    #     self._trigger_proposal_calculations([x[0] for x in swap_list])
    #     work_pairs = self._receive_works(swap_list)
    #     acceptance_probabilities = [self._calculate_acceptance_probability(*work_pair)
    #                                 for work_pair in work_pairs]
    #     accepted = numpy.random.uniform(size=len(swap_list)) < acceptance_probabilities
    #     self._trigger_exchanges(swap_list, accepted)

    # def _trigger_exchanges(self, swap_list):

    #     self._send_exchange_requests(swap_list)
    #     results = self._receive_exchange_results(swap_list)
    #     return results

    # def _send_exchange_requests(self, swap_list):
        
    #     for r1, r2 in swap_list:
    #         self.comm.send(Parcel(self.id_offset, 'replica{}'.format(r1), 
    #                               ExchangeRequest(r2, 'MPISimpleReplicaExchanger')), 
    #                        dest=self.id_offset+r1)

    # def _receive_exchange_results(self, swap_list):

    #     return [self.comm.recv(source=self.id_offset+i) for i in swap_list]

    # def _trigger_proposal_calculations(swap_list):

    #     for r1, r2 in swap_list:
    #         self.comm.send(CalculateProposalRequest(self.id_offset, minion='proposer{}'.format(r1), 
    #                                                 orig_replica=r2),
    #                        dest=self.id_offset + r1)
    #         self.comm.send(CalculateProposalRequest(self.id_offset, minion='proposer{}'.format(r2), 
    #                                                 orig_replica=r1),
    #                        dest=self.id_offset + r1)        
            
    # def _calculate_swap_list(self, i):
    #     '''
    #     This can be modified to implement, e.g., Yannick's convective RE
    #     '''

    #     swap_list = range(self._n_replicas - 1)[self.exchange_counter % 2 != 0::2]
    #     if len(swap_list) == 0:
    #         swap_list.append(0)
        
    #     return swap_list

    # def _send_border_replica_sample_requests(self, swap_list):

    #     if len(swap_list) > 0:
    #         sampling = []
    #         if not 0 in swap_list:
    #             sampling.append(0)
    #             self._send_sample_requests(targets=[0])
    #         if not self._n_replicas - 2 in swap_list and self._n_replicas - 2 != 0:
    #             sampling.append(self._n_replicas - 1)
    #             self._send_sample_requests(targets=[self._n_replicas - 1])

            # stats = self._receive_sample_stats(sampling)
            # self._update_sampler_stats(stats)

    # def _dump_sampler_stats(self, i, status_interval, samples_folder):
    #     '''
    #     TODO: put all the statistics stuff in an object StatisticsPrinter / Dumper
    #     '''
        
    #     if i % status_interval == 0:
            
    #         import os
    #         from csv import DictWriter, writer
            
    #         self._send_sampler_stats_requests()
    #         allstats = self._receive_sampler_stats()
    #         for j, stats in enumerate(allstats):
    #             if i == 0:
    #                 os.system('mkdir '+ samples_folder + 'sampling_statistics/')
    #             with open(samples_folder + '/sampling_statistics/sampler{}.txt'.format(j),'a') as opf:
    #                 stats_writer = DictWriter(opf, fieldnames=['MC sample'] + sorted(stats.keys()), delimiter='\t')
    #                 if i == 0:
    #                     stats_writer.writeheader()
    #                 stats.update(**{'MC sample': i})
    #                 stats_writer.writerow(stats)
    #         with open(samples_folder + '/sampling_statistics/re_acceptance_rates.txt', 'a') as opf:
    #             re_fields = ['{}<->{}'.format(k, k+1) for k in xrange(len(allstats) - 1)]
    #             stats_writer = DictWriter(opf, fieldnames=['MC sample'] + re_fields,
    #                                       delimiter='\t')
    #             if i == 0:
    #                 stats_writer.writeheader()
    #             re_stats = {field: x for (field, x) in zip(re_fields, self.swap_acceptance_rates)}
    #             re_stats.update(**{'MC sample': i})
    #             stats_writer.writerow(re_stats)
        
            
    def run(self, n_iterations, swap_interval=5, status_interval=100, samples_folder=None, 
            dump_interval=250, dump_step=5):

        for i in xrange(n_iterations):
            if i % swap_interval == 0 and i > 0:
                # swap_list = self._calculate_swap_list(i)
                # results = self._trigger_exchanges(swap_list)
                # # self._update_stats(results)
                # self._send_border_replica_sample_requests(swap_list)
                # self.sampling_statistics.update(self.step)

                # swap_list = self._calculate_swap_list(i)
                # results = self._perform_exchanges(swap_list)
                # # self.statistics.update
                # self._update_stats(results)
                # self._send_border_replica_sample_requests(swap_list)
                pass
            else:
                self._send_sample_requests()
                self.sampling_statistics.update(self.step)

            self.step += 1

            # if i % status_interval == 0:
            #     self.statistics.


    def _send_sample_requests(self, targets=None):

        recipients = xrange(self._n_replicas) if targets is None else targets

        for r in recipients:
            parcel = Parcel(self.name, 'replica{}'.format(r+1), SampleRequest(self.name))
            self._comm.send(parcel, dest='replica{}'.format(self.id_offset + r))

    # def _send_exchange_requests(self, swap_list):
        
    #     for i in swap_list:
    #         self._comm.send(ExchangeRequest(self.id_offset+i+1, 'MPISimpleReplicaExchanger'), 
    #                        dest=self.id_offset+i)

    # def _send_dump_samples_request(self, samples_folder, smin, smax, dump_step):

    #     for i in xrange(self._n_replicas):
    #         self._comm.send(DumpSamplesRequest(samples_folder, smin, smax, dump_step),
    #                        dest=self.id_offset+i)

    # def _receive_exchange_results(self, swap_list):

    #     return [self._comm.recv(source=self.id_offset+i) for i in swap_list]
        
    def terminate_replicas(self):

        for r in xrange(self._n_replicas):
            parcel = Parcel(self.name, 'replica{}'.format(self.id_offset+r), 
                            DieRequest(self.name))
            self._comm.send(parcel, dest='replica{}'.format(self.id_offset + r))

    # def get_replica_state(self, id):

    #     self._comm.send(GetStateRequest(self.id_offset - 1), dest=self.id_offset + id)
    #     res = self._comm.recv(source=self.id_offset + id)

    #     return res

    # def get_current_state(self):

    #     return EnsembleState([self.get_replica_state(i) for i in xrange(self._n_replicas)])
