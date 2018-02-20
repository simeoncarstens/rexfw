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
        self._state = None
        
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

        self.energy_trace = []
        self.ctr = 0

        self.sampler_stats = []

        ## Hack to ensure compatibility with ISD2 PDFs
        self._wrap_pdf()
        
        self._process = None

        self._request_processing_table = {}
        self._setup_request_processing_table()

    def _wrap_pdf(self):

        from isd2.pdf import AbstractISDPDF
        if isinstance(self.pdf, AbstractISDPDF):
            from isd2.samplers.pdfwrapper import PDFWrapper
            self.pdf = PDFWrapper(self.pdf)

    def _setup_request_processing_table(self):

        self._request_processing_table = dict(
            SampleRequest='self._sample({})',
            SendStatsRequest='self._send_stats({})',
            ProposeRequest='self._propose({})',
            AcceptBufferedProposalRequest='self._accept_buffered_proposal({})',
            SendGetStateAndEnergyRequest='self._send_get_state_and_energy_request({})',
            StoreStateEnergyRequest='self._store_state_energy({})',
            GetStateAndEnergyRequest='self._send_state_and_energy({})',
            DumpSamplesRequest='self._dump_samples({})',
            DoNothingRequest='self._do_nothing({})',
            DieRequest='-1')

    def _do_nothing(self, request):
        pass
        
    def _setup_sampler(self):

        from copy import deepcopy
        self._sampler = self.sampler_class(self.pdf, deepcopy(self.state), 
                                           **self.sampler_params)

    def _setup_pdf(self):
        pass

    @property
    def state(self):
        return self._state
    @state.setter
    def state(self, value):
        self._state = value
        if not self._sampler is None:
            self._sampler._state = value

    def _send_state_and_energy(self, request):

        # request = StoreStateEnergyRequest(request.sender, self.state, self.energy)
        # self._comm.send(Parcel(self.name, request.sender, request), request.sender)
        ## above was wrong, but didn't lead to any consequences
        
        new_request = StoreStateEnergyRequest(self.name, self.state, self.energy)
        self._comm.send(Parcel(self.name, request.sender, new_request), request.sender)

    def _send_get_state_and_energy_request(self, request):

        self._current_master = request.sender
        self._comm.send(Parcel(self.name, request.partner, GetStateAndEnergyRequest(self.name)), 
                        request.partner)    

    def _store_state_energy(self, request):

        self._buffered_partner_state = request.state
        self._buffered_partner_energy = request.energy
        from rexfw.replicas.requests import DoNothingRequest
        parcel = Parcel(self.name, self._current_master, DoNothingRequest(self.name))
        self._comm.send(parcel, dest=self._current_master)
    
    def _sample(self, request):

        from copy import deepcopy
        res = deepcopy(self._sampler.sample())
        self.state = res
        self.samples.append(deepcopy(res))
        self.sampler_stats.append([self.ctr, self._sampler.get_last_draw_stats()])

        if self.ctr % 2 == 0:
            self.energy_trace.append(self.energy)
        self.ctr += 1        
        
    def _send_stats(self, request):

        parcel = Parcel(self.name, request.sender, self.sampler_stats)
        self._comm.send(parcel, request.sender)
        self.sampler_stats = []

    def _dump_samples(self, request):
        import numpy, os

        filename = '{}samples_{}_{}-{}.pickle'.format(request.samples_folder, 
                                                      self.name, 
                                                      request.s_min + request.offset, 
                                                      request.s_max + request.offset)
        with open(filename, 'w') as opf:
            from cPickle import dump
            dump(self.samples[::request.dump_step], opf, 2)

        self.samples = []
        self._dump_energies(request)

    def _dump_energies(self, request):

        import numpy, os
        
        Es_folder = request.samples_folder[:-len('samples/')] + 'energies/'
        Es_filename = Es_folder + self.name + '.npy'
        if os.path.exists(Es_filename):
            self.energy_trace = list(numpy.load(Es_filename)) + self.energy_trace
        numpy.save(Es_filename, numpy.array(self.energy_trace))
        self.energy_trace = []
                
    def process_request(self, request):

        dummy = None
        return eval(self._request_processing_table[request.__class__.__name__].format('request'))
    
    def _propose(self, request):

        proposal = self._calculate_proposal(request)
        self._send_works_heats(proposal)
        self._buffered_proposal = proposal[-1]

    def _send_works_heats(self, proposal):
        
        self._comm.send(Parcel(self.name, self._current_master, 
                               (float(proposal.work), float(proposal.heat))), 
                               self._current_master)
        
    def _calculate_proposal(self, request):

        partner_name = request.partner
        params = request.params
        proposer_params = params.proposer_params
        self._current_master = request.sender

        proposer = list(set(self.proposers.keys()).intersection(set(params.proposers)))[-1]
        self.proposers[proposer].partner_name = partner_name
        proposal = self.proposers[proposer].propose(self, 
                                                    self._buffered_partner_state,
                                                    self._buffered_partner_energy,
                                                    proposer_params)

        return proposal
        
    def _accept_buffered_proposal(self, request):

        from copy import deepcopy
        
        if request.accept:
            self.state = self._buffered_proposal
        self.samples.append(deepcopy(self.state))
        from rexfw.replicas.requests import DoNothingRequest
        self._comm.send(Parcel(self.name, self._current_master, DoNothingRequest(self.name)), 
                        self._current_master)
        self.energy_trace.append(self.energy)
        self.ctr += 1
        
    def _send_energy(self, request):

        state = request.state
        E = self.get_energy() if state is None else self.get_energy(state) 
        parcel = Parcel(self.name, request.sender, E)
        self._comm.send(parcel, dest=request.sender)

    @property
    def energy(self):

        return self.get_energy(self.state)
        
    def get_energy(self, state):

        if 'position' in dir(state):
            return -self.pdf.log_prob(state.position)
        else:
            return -self.pdf.log_prob(state)
