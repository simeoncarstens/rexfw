'''
Replica classes which sample from a single PDF
'''

from abc import ABCMeta, abstractmethod, abstractproperty

from rexfw import Parcel


class Replica(object):

    def __init__(self, name, state, pdf, pdf_params, 
                 sampler_class, sampler_params, exchangers, comm):

        self.name = name
        self.samples = []
        self._sampler = None
        
        self.state = state
        self.pdf = pdf
        self.pdf_params = pdf_params
        self.sampler_class = sampler_class
        self.sampler_params = sampler_params
        self.exchangers = exchangers

        self._comm = comm
        self.simulating = False

        self._setup_pdf()
        self._setup_sampler()

        ## Hack to ensure compatibility with ISD2 PDFs
        from isd2.pdf import AbstractISDPDF
        if isinstance(self.pdf, AbstractISDPDF):
            from isd2.samplers.pdfwrapper import PDFWrapper
            self.pdf = PDFWrapper(self.pdf)
        
        self._process = None

        self._request_processing_table = {}
        self._setup_request_processing_table()

    def _setup_request_processing_table(self):

        self._request_processing_table = dict(
            SampleRequest='self._sample({})',
            SendStatsRequest='self._send_stats({})',
            SamplerStatsRequest='self._send_sampler_stats({})',
            ExchangeRequest='self._perform_exchange({})',
            GetStateRequest='self._send_state({})',
            SetStateRequest='self._set_state_from_request({})',
            GetEnergyRequest='self._send_energy({})',
            DumpSamplesRequest='self._dump_samples({})',
            DieRequest='-1')
        
    def _setup_sampler(self):

        self._sampler = self.sampler_class(self.pdf, self.state, 
                                           **self.sampler_params)

    def _setup_pdf(self):
        pass

    @property
    def state(self):
        return self.samples[-1]
    @state.setter
    def state(self, value):
        self.samples.append(value)
        if not self._sampler is None:
            self._sampler._state = value

    # def _set_state_from_request(self, request):
    #     self.state = request.state

    # def _send_state(self, request):
    #     return Parcel(self.id, request.dest, self.state)

    def _sample(self, request):
        from copy import deepcopy
        res = deepcopy(self._sampler.sample())
        self.state = res

    def _send_stats(self, request):

        parcel = Parcel(self.name, request.sender, self._sampler.get_last_draw_stats())
        self._comm.send(parcel, request.sender)

    # def _dump_samples(self, request):
    #     smin = request.smin
    #     smax = request.smax
        
    #     with open(request.samples_folder + 'samples_replica'+str(self.id)+'_'+str(smin)+'-'+str(smax)+'.pickle', 'w') as opf:
    #         from cPickle import dump
    #         dump(self.samples[request.smin:request.smax:request.dump_step], opf, 2)

    # def _send_sampler_stats(self, request):

    #     return Parcel(self.id, 0, self._sampler.sampling_stats)
    
    def process_request(self, request):

        dummy = None
        return eval(self._request_processing_table[request.__class__.__name__].format('request'))
    
    # def _listen(self):

    #     while True:
    #         request = self._receive_request()
    #         if self._process_request(request) == -1:
    #             break

    # def listen(self):

    #     from threading import Thread

    #     self._thread = Thread(target=self._listen)
    #     self._thread.start()

    def _perform_exchange(self, request):
        partner = request.partner
        exchanger = self.exchangers[request.exchanger]
        params = request.params
        accepted = exchanger.exchange(self, partner, params)
        self.comm.send(Parcel(self.name, request.sender, ExchangeResult(accepted)), 
                       dest=request.sender)

    # def _receive_request(self):

    #     return self.comm.recv(source=MPI.ANY_SOURCE)

    # def _send_state(self, request):

    #     self.comm.send(Parcel(self.id, 'replica{}'.format(requesting_replica_id), self.state),
    #                    dest=request.requesting_replica_id)

    def _send_energy(self, request):

        state = request.state
        E = self.get_energy() if state is None else self.get_energy(state) 
        parcel = Parcel(self.name, request.sender, E)
        self.comm.send(parcel, dest=request.sender)

    @property
    def energy(self):

        return self.get_energy(self.state)
        
    def get_energy(self, state):

        return -self.pdf.log_prob(state.position)
        
    # def _send_sample_stats(self, accepted):

    #     self.comm.send(Parcel(self.id, request.sender, accepted),
    #                    dest=request.sender)

    # def _send_sampler_stats(self):

    #     self.comm.send(Parcel(self.id, request.sender, self._sampler.sampling_stats), 
    #                    dest=request.sender)


# class AbstractSimpleReplica(AbstractReplica):

#     def __init__(self, *args):

#         super(AbstractSimpleReplica, self).__init__(*args)
        
#         self.request_up_to_date = False

#     def _receive_request(self):

#         if self.request_up_to_date:
#             self.request_up_to_date = False
#             return self.request
#         else:
#             return

#     def terminate(self):

#         self.request = DieRequest()
#         self.request_up_to_date = True


# class AbstractMPIReplica(AbstractReplica):

#     comm = MPICommunicator()
