'''
Replica classes which sample from a single PDF
'''

from abc import abstractmethod, abstractproperty

from rexfw import Parcel
from rexfw.replicas.requests import GetStateAndEnergyRequest, StoreStateEnergyRequest

class Replica(object):

    _current_master = None
    
    def __init__(self, name, state, pdf, sampler_class, sampler_params, 
                 proposers, output_folder, comm):
        '''
        Default replica class

        :param name: name of the replica object
        :type name: str

        :param state: initial state
        :type state: up to you

        :param pdf: a probability density function exposing the interface
                    defined in :class:`.AbstractPDF`
        :type pdf: :class:`.AbstractPDF`

        :param sampler_class: a class (not an instance) exposing the interface
                              defined in :class:`.AbstractSampler`
        :type sampler: :class:`.AbstractSampler`

        :param sampler_params: a dictionary holding any additional parameters
                               needed to instantiate the sampler object
        :type sampler_params: dict

        :param proposers: a dictionary containing proposers for the replica
                          with keys being the proposer names
        :type proposers: dict

        :param output_folder: the folder where simulation output will be stored
        :type output_folder: str

        :param comm: a communicator object to communicate with the master object
                     and other replicas
        :type comm: :class:`.AbstractCommunicator`
        '''

        self.name = name
        self.samples = []
        self._sampler = None
        self._state = None
        
        self.state = state
        self.pdf = pdf
        self.sampler_class = sampler_class
        self.sampler_params = sampler_params
        self.proposers = proposers
        self.output_folder = output_folder
        self._comm = comm
        self._setup_sampler()

        self.energy_trace = []
        self._n_samples_drawn = 0

        self.sampler_stats = []

        self._request_processing_table = {}
        self._setup_request_processing_table()

    def _setup_request_processing_table(self):
        '''
        Sets up a dictionary containing possible incoming request objects as 
        keys and string templates for the function calls to process the request
        as values
        '''

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
        '''
        Does nothing :-) Serves to synchronize communication with the master object

        :param request: a :class:`.DoNothingRequest`
        :type request: :class:`.DoNothingRequest`
        '''
        pass
        
    def _setup_sampler(self):
        '''
        Instantiates the sampler object from the sampler class given in
        :meth:`rexfw.replicas.Replica.__init__`
        '''

        from copy import deepcopy
        self._sampler = self.sampler_class(self.pdf, deepcopy(self.state), 
                                           **self.sampler_params)

    @property
    def state(self):
        '''
        Returns the current state of the replica (and thus the sampler)

        :return: current state of replica (and sampler)
        :rtype: depends on your application
        ''' 
        return self._state
    @state.setter
    def state(self, value):
        '''
        Sets the replica and sampler state

        :param value: value to set states to
        :type value: depends on your application
        '''
        self._state = value
        if not self._sampler is None:
            self._sampler._state = value

    def _send_state_and_energy(self, request):
        '''
        Sends the current state and energy to another replica and makes it store them

        :param request: a request object telling this replica which other replica
                        to send state and energy to
        :type request: :class:`.GetStateAndEnergyRequest`
        '''
        
        new_request = StoreStateEnergyRequest(self.name, self.state, self.energy)
        self._comm.send(Parcel(self.name, request.sender, new_request), request.sender)

    def _send_get_state_and_energy_request(self, request):
        '''
        Sends a :class:`.GetStateAndEnergyRequest` to another replica given in the request
        parameter

        :param request: a request object telling this replica which other replica
                        to ask for its state and energy
        :type request: :class:`.SendGetStateAndEnergyRequest`
        '''
        self._current_master = request.sender
        self._comm.send(Parcel(self.name, request.partner, GetStateAndEnergyRequest(self.name)), 
                        request.partner)    

    def _store_state_energy(self, request):
        '''
        Stores state and energy given in request parameter. Also sends a 
        :class:`.DoNothingRequest` to the master object. This is neccessary to
        keep communication in sync
        

        :param request: a request object containing current state and energy of a different
                        replica
        :type request: :class:`.StoreStateEnergyRequest`
        '''
        self._buffered_partner_state = request.state
        self._buffered_partner_energy = request.energy
        from rexfw.replicas.requests import DoNothingRequest
        parcel = Parcel(self.name, self._current_master, DoNothingRequest(self.name))
        self._comm.send(parcel, dest=self._current_master)
    
    def _sample(self, request):
        '''
        Makes the sampler draw a sample, stores it, stores sampling statistics,
        increases the sample counter and updates the energy trace list

        :param request: a request object asking this replica to do all of the above
        :type request: :class:`.SampleRequest`
        '''
        from copy import deepcopy
        res = deepcopy(self._sampler.sample())
        self.state = res
        self.samples.append(deepcopy(res))
        self.sampler_stats.append([self._n_samples_drawn, self._sampler.last_draw_stats])
        self._update_energy_trace()
        self._increase_sample_counter()
        
    def _send_stats(self, request):
        '''
        Sends sampling statistics to master object. Also empties sampling stats list

        :param request: a request object asking this replica to do the above
        :type request: :class:`.SendStatsRequest`
        '''
        
        parcel = Parcel(self.name, request.sender, self.sampler_stats)
        self._comm.send(parcel, request.sender)
        self.sampler_stats = []

    def _dump_samples(self, request):
        '''
        Writes samples and energies to a file, then empties list of stored samples
        in memory

        :param request: a request object containing information which samples to write
        :type request: :class:`.DumpSamplesRequest`
        '''
        import numpy, os

        filename = '{}samples/samples_{}_{}-{}.pickle'.format(self.output_folder, 
                                                              self.name, 
                                                              request.s_min + request.offset, 
                                                              request.s_max + request.offset)
        with open(filename, 'w') as opf:
            from pickle import dump
            dump(self.samples[::request.dump_step], opf, 2)

        self.samples = []
        self._dump_energies()

    def _dump_energies(self):
        '''
        Updates files with replica energies and empties list of stored energies
        '''
        import numpy, os
        
        Es_folder = self.output_folder + 'energies/'
        Es_filename = Es_folder + self.name + '.npy'
        if os.path.exists(Es_filename):
            self.energy_trace = list(numpy.load(Es_filename)) + self.energy_trace
        numpy.save(Es_filename, numpy.array(self.energy_trace))
        self.energy_trace = []
                
    def process_request(self, request):
        '''
        Processes a request by looking up the corresponding function in the
        request processing table

        :param request: request object to process
        :type request: depends
        '''

        return eval(self._request_processing_table[request.__class__.__name__].format('request'))
    
    def _propose(self, request):
        '''
        Calculates a swap proposal state and sends works and heats to master object

        :param request: a request object containing information needed to calculate
                        the proposal
        :type request: :class:`.ProposeRequest`
        '''

        proposal = self._calculate_proposal(request)
        self._send_works_heats(proposal)
        self._buffered_proposal = proposal[-1]

    def _send_works_heats(self, proposal):
        '''
        Sends works and heats corresponding to a swap proposal to the master object

        :param proposal: a state proposed for swapping
        :type proposal: depends on your application
        '''
        self._comm.send(Parcel(self.name, self._current_master, 
                               (float(proposal.work), float(proposal.heat))), 
                               self._current_master)

    def _pick_proposer(self, params):
        '''
        Picks proposer from this replicas' proposer list

        :param params: an object holding parameters defining the exchange to be performed
        :type params: :class:`.ExchangeParams`

        :return: the proposer object which will be used to calculate the proposal
        :rtype: :class:`.AbstractProposer`
        '''

        return list(set(self.proposers.keys()).intersection(set(params.proposers)))[-1]        
        
    def _calculate_proposal(self, request):
        '''
        Calculates a proposal for a replica and using information given in request
        parameter

        :param request: a request object containing the name of the replica to which
                        a state will be proposed to and other information needed to 
                        calculate the proposal
        :type request: :class:`.ProposeRequest`

        :return: a swap proposal state
        :rtype: depends on your application
        '''

        partner_name = request.partner
        params = request.params
        proposer_params = params.proposer_params
        self._current_master = request.sender

        proposer = self._pick_proposer(params)
        self.proposers[proposer].partner_name = partner_name
        proposal = self.proposers[proposer].propose(self, 
                                                    self._buffered_partner_state,
                                                    self._buffered_partner_energy,
                                                    proposer_params)

        return proposal
        
    def _accept_buffered_proposal(self, request):
        '''
        If the information in the request object says so, accepts a proposal
        by setting the replica state to the buffered proposal and, in any case,  
        appending the current replica state to the list of stored samples. Also
        syncs communication with master object and updates stored replica energies 
        and the sample counter

        :param request: a request containing information whether the proposal
                        should be accepted or not
        :type request: :class:`.AcceptBufferedProposalRequest`
        '''

        from copy import deepcopy
        
        if request.accept:
            self.state = self._buffered_proposal
        self.samples.append(deepcopy(self.state))
        from rexfw.replicas.requests import DoNothingRequest
        self._comm.send(Parcel(self.name, self._current_master, DoNothingRequest(self.name)), 
                        self._current_master)
        self._update_energy_trace()
        self._increase_sample_counter()

    def _increase_sample_counter(self):
        '''
        Guess what - increases the sample counter!
        '''

        self._n_samples_drawn += 1

    def _update_energy_trace(self):
        '''
        Updates the list of stored replica energies
        '''
        
        self.energy_trace.append(self.energy)
        
    @property
    def energy(self):
        '''
        Returns the replica energy, that is, the negative log-probability of the replica's
        PDF evaluated at the current state

        :return: the current replica energy
        :rtype: depends on your application
        '''

        return self.get_energy(self.state)
        
    def get_energy(self, state):
        '''
        Calculates replica energy (negative log-probability) for a given state

        :param state: state for which to evaluate the negative log-probability of
                      the replica's PDF
        :type state: depends on your application
        '''
        return -self.pdf.log_prob(state)
