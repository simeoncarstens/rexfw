'''
Master classes implementing exchange criteria for RE and derived algorithms
'''

from rexfw import Parcel
from rexfw.remasters.requests import SampleRequest, DieRequest, ProposeRequest, AcceptBufferedProposalRequest
from rexfw.remasters.requests import GetStateAndEnergyRequest_master, SendGetStateAndEnergyRequest

from collections import namedtuple

ExchangeParams = namedtuple('ExchangeParams', 'proposers')

REStats = namedtuple('REStats', 'accepted')

class ReplicaExchangeMaster(object):

    def __init__(self, name, replica_names, comm, sampling_statistics=None, swap_statistics=None, id_offset=1):

        self.name = name
        self.replica_names = replica_names
        self._n_replicas = len(self.replica_names)
        self.sampling_statistics = sampling_statistics
        self.swap_statistics = swap_statistics
        self._comm = comm
        self.step = 0

        self.sampling_statistics.initialize(self.replica_names)
        
    def _send_propose_request(self, r1, r2, params):
        
        request = ProposeRequest(self.name, r2, params)
        self._comm.send(Parcel(self.name, r1, request), dest=r1)

    def _perform_exchanges(self, swap_list):

        works = [[0.0, 0.0]] * len(swap_list)
        for i, (r1, r2, params) in enumerate(swap_list):
            self._comm.send(Parcel(self.name, r2, SendGetStateAndEnergyRequest(self.name, r1)), r2)
            self._comm.send(Parcel(self.name, r1, SendGetStateAndEnergyRequest(self.name, r2)), r1)

            ## Receives a None from r1 and r2; sent once buffered state / energies have been set
            ## this is to sync everything and really hacky
            self._comm.recv(source=r1)
            self._comm.recv(source=r2)

            self._send_propose_request(r1, r2, params)
            self._send_propose_request(r2, r1, params)

        for i, (r1, r2, params) in enumerate(swap_list):
            works[i][0] = self._comm.recv(source=r1).data
            works[i][1] = self._comm.recv(source=r2).data

        for i, (r1, r2, params) in enumerate(swap_list):
            self._send_propose_request(r2, r1, params)
            works[i][1] = self._comm.recv(source=r2).data

        import numpy
        acc = numpy.exp(-numpy.sum(works,1)) > numpy.random.uniform(size=len(works))
        
        for i, (r1, r2, params) in enumerate(swap_list):
            oui = acc[i]
            
            if acc:
                parcel = Parcel(self.name, r1, AcceptBufferedProposalRequest(self.name, True))
                self._comm.send(parcel, r1)
                parcel = Parcel(self.name, r2, AcceptBufferedProposalRequest(self.name, True))
                self._comm.send(parcel, r2)
            else:
                parcel = Parcel(self.name, r1, AcceptBufferedProposalRequest(self.name, False))
                self._comm.send(parcel, r1)
                parcel = Parcel(self.name, r2, AcceptBufferedProposalRequest(self.name, False))
                self._comm.send(parcel, r2)

        return acc
        
              
            
    def _calculate_swap_list(self, i):
        '''
        This can be modified to implement, e.g., Yannick's convective RE
        '''

        # swap_list = range(self._n_replicas - 1)[self.exchange_counter % 2 != 0::2]
        # if len(swap_list) == 0:
        #     swap_list.append(0)

        swap_list = [['replica1', 'replica2', ExchangeParams(('reprop1', 'reprop2'))]]
        
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
                swap_list = self._calculate_swap_list(i)
                results = self._perform_exchanges(swap_list)
                for j, (r1, r2, _) in enumerate(swap_list):
                    self.swap_statistics.update(i, {r1+'_'+r2: REStats(results[j])})
                no_ex_replicas = self._get_no_ex_replicas(swap_list)
                self._send_sample_requests(no_ex_replicas)
                self.sampling_statistics.update(self.step, no_ex_replicas)
            else:
                self._send_sample_requests(self.replica_names)
                self.sampling_statistics.update(self.step, self.replica_names)

            self.step += 1


    def _send_sample_requests(self, targets):

        for t in targets:
            parcel = Parcel(self.name, t, SampleRequest(self.name))
            self._comm.send(parcel, dest=t)

    # def _send_dump_samples_request(self, samples_folder, smin, smax, dump_step):

    #     for i in xrange(self._n_replicas):
    #         self._comm.send(DumpSamplesRequest(samples_folder, smin, smax, dump_step),
    #                        dest=self.id_offset+i)
        
    def terminate_replicas(self):

        for r in self.replica_names:
            parcel = Parcel(self.name, r, DieRequest(self.name))
            self._comm.send(parcel, dest=r)

