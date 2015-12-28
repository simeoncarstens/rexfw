'''
Master classes implementing exchange criteria for RE and derived algorithms
'''

from rexfw import Parcel
from rexfw.remasters.requests import SampleRequest, DieRequest, ExchangeRequest


class ReplicaExchangeMaster(object):

    # __metaclass__ = ABCMeta

    def __init__(self, name, replica_names, comm, sampling_statistics=None, swap_statistics=None, id_offset=1):

        self.name = name
        self.replica_names = replica_names
        self._n_replicas = len(self.replica_names)
        self.sampling_statistics = sampling_statistics
        self.swap_statistics = swap_statistics
        self._comm = comm
        self.step = 0

        self.sampling_statistics.initialize(self.replica_names)
        
    def _trigger_exchanges(self, swap_list):

        self._send_exchange_requests(swap_list)
        results = self._receive_exchange_results(swap_list)

        return results

    def _send_exchange_requests(self, swap_list):
        
        for r1, r2, ex in swap_list:
            request = ExchangeRequest(self.name, r2, ex, None)
            self._comm.send(Parcel(self.name, r1, request), dest=r1)

    def _receive_exchange_results(self, swap_list):

        return [self._comm.recv(source=r1) for r1, r2, _ in swap_list]
            
    def _calculate_swap_list(self, i):
        '''
        This can be modified to implement, e.g., Yannick's convective RE
        '''

        # swap_list = range(self._n_replicas - 1)[self.exchange_counter % 2 != 0::2]
        # if len(swap_list) == 0:
        #     swap_list.append(0)

        swap_list = [['replica1', 'replica2', 'rexex1']]
        
        return swap_list

    def _get_no_ex_replicas(self, swap_list):

        ex_replicas = [[x[0], x[1]] for x in swap_list]
        ex_replicas = [x for z in ex_replicas for x in z]
        return list(set(ex_replicas).difference(self.replica_names))

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

    def run(self, n_iterations, swap_interval=5, status_interval=100, samples_folder=None, 
            dump_interval=250, dump_step=5):

        for i in xrange(n_iterations):
            if i % swap_interval == 0 and i > 0:
                # swap_list = self._calculate_swap_list(i)
                # results = self._trigger_exchanges(swap_list)
                # # self._update_stats(results)
                # no_ex_replicas = self._no_ex_replicas(swap_list)
                # self._send_sample_requests(no_ex_replicas)
                # self.sampling_statistics.update(self.step, no_ex_replicas)

                # swap_list = self._calculate_swap_list(i)
                # results = self._perform_exchanges(swap_list)
                # # self.statistics.update
                # self._update_stats(results)
                # self._send_border_replica_sample_requests(swap_list)
                pass
            else:
                self._send_sample_requests(self.replica_names)
                self.sampling_statistics.update(self.step, self.replica_names)

            self.step += 1

            # if i % status_interval == 0:
            #     self.statistics.


    def _send_sample_requests(self, targets):

        for t in targets:
            parcel = Parcel(self.name, t, SampleRequest(self.name))
            self._comm.send(parcel, dest=t)

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

        for r in self.replica_names:
            parcel = Parcel(self.name, r, DieRequest(self.name))
            self._comm.send(parcel, dest=r)

    # def get_replica_state(self, id):

    #     self._comm.send(GetStateRequest(self.id_offset - 1), dest=self.id_offset + id)
    #     res = self._comm.recv(source=self.id_offset + id)

    #     return res

    # def get_current_state(self):

    #     return EnsembleState([self.get_replica_state(i) for i in xrange(self._n_replicas)])
