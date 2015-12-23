'''
Small request classes which communicate the needs and deeds of replicas
'''

class AbstractReplicaRequest(object):
    pass



class GetSampleListRequest(AbstractReplicaRequest):
    pass


class DumpSamplesRequest(AbstractReplicaRequest):

    def __init__(self, samples_folder, smin, smax, dump_step=1):

        self.samples_folder = samples_folder
        self.smin = smin
        self.smax = smax
        self.dump_step = dump_step
                

class NullRequest(AbstractReplicaRequest):
    pass


class DieRequest(AbstractReplicaRequest):
    pass


class ExchangeRequest(AbstractReplicaRequest):

    def __init__(self, partner_id, exchanger_name):

        self.partner_id = partner_id
        self.exchanger_name = exchanger_name
        

class GetStateRequest(AbstractReplicaRequest):

    def __init__(self, requesting_replica_id):

        self.requesting_replica_id = requesting_replica_id


class GetEnergyRequest(AbstractReplicaRequest):

    def __init__(self, requesting_replica_id, state=None):

        self.requesting_replica_id = requesting_replica_id
        self.state = state
        

class SetStateRequest(AbstractReplicaRequest):

    def __init__(self, state):

        self.state = state
