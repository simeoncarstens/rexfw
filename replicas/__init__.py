'''
Replica classes which sample from a single PDF
'''

from abc import ABCMeta, abstractmethod, abstractproperty

from rexfw import Parcel
from rexfw.replicas.requests import GetStateAndEnergyRequest, StoreStateEnergyRequest

class Replica(object):

    _current_master = None
    
    def __init__(self, name, state, pdf, pdf_params, 
                 sampler_class, sampler_params, proposers, comm):

        self.name = name
        self.samples = []
        self._sampler = None
        
        self.state = state
        self.pdf = pdf
        self.pdf_params = pdf_params
        self.sampler_class = sampler_class
        self.sampler_params = sampler_params
        self.proposers = proposers

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
            ProposeRequest='self._propose({})',
            AcceptBufferedProposalRequest='self._accept_buffered_proposal({})',
            SendGetStateAndEnergyRequest='self._send_get_state_and_energy_request({})',
            StoreStateEnergyRequest='self._store_state_energy({})',
            GetStateAndEnergyRequest='self._send_state_and_energy({})',
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

    def _send_state_and_energy(self, request):

        self._current_master = request.sender
        request = StoreStateEnergyRequest(request.sender, self.state, self.energy)
        self._comm.send(Parcel(self.name, request.sender, request), request.sender)

    def _send_get_state_and_energy_request(self, request):

        self._comm.send(Parcel(self.name, request.partner, GetStateAndEnergyRequest(self.name)), 
                        request.partner)    

    def _store_state_energy(self, request):

        self._buffered_partner_state = request.state
        self._buffered_partner_energy = request.energy
        self._comm.send(self._current_master, dest='master0')
    
    def _sample(self, request):
        from copy import deepcopy
        res = deepcopy(self._sampler.sample())
        self.state = res

    def _send_stats(self, request):

        parcel = Parcel(self.name, request.sender, self._sampler.get_last_draw_stats())
        self._comm.send(parcel, request.sender)

    def _dump_samples(self, request):

        filename = '{}samples_{}_{}-{}.pickle'.format(request.samples_folder, 
                                                      self.name, 
                                                      request.s_min, 
                                                      request.s_max)
        with open(filename, 'w') as opf:
            from cPickle import dump
            dump(self.samples[request.s_min:request.s_max:request.dump_step], opf, 2)
    
    def process_request(self, request):

        dummy = None
        return eval(self._request_processing_table[request.__class__.__name__].format('request'))
    
    def _propose(self, request):

        partner_name = request.partner
        params = request.params
        proposer_params = params.proposer_params
        self._current_master = request.sender
        
        proposer = list(set(self.proposers.keys()).intersection(set(params.proposers)))[-1]
        proposal = self.proposers[proposer].propose(self, 
                                                    self._buffered_partner_state,
                                                    self._buffered_partner_energy,
                                                    proposer_params)
        self._comm.send(Parcel(self.name, self._current_master, float(proposal.work)), self._current_master)
        self._buffered_proposal = proposal[-1]

    def _accept_buffered_proposal(self, request):

        from copy import deepcopy
        
        if request.accept:
            self.state = self._buffered_proposal
        self.samples.append(deepcopy(self.state))
        
    def _send_energy(self, request):

        state = request.state
        E = self.get_energy() if state is None else self.get_energy(state) 
        parcel = Parcel(self.name, request.sender, E)
        self._comm.send(parcel, dest=request.sender)

    @property
    def energy(self):

        return self.get_energy(self.state)
        
    def get_energy(self, state):

        return -self.pdf.log_prob(state.position)
