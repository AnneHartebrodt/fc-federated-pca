import shutil
import threading
import time
import jsonpickle
import jsonpickle.ext.numpy as jsonpickle_numpy
jsonpickle_numpy.register_handlers()
import yaml
from app.algo import local_computation, global_aggregation
from app.Aggregator_FC_Federated_PCA import AggregatorFCFederatedPCA
from app.Client_FC_FederatedPCA import ClientFCFederatedPCA
from app.Steps import Step

from app.QR_params import QR


class AppLogic:

    def __init__(self):
        # === Status of this app instance ===

        # Indicates whether there is data to share, if True make sure self.data_out is available
        self.status_available = False

        # Will stop execution when True
        self.status_finished = False

        # === Data ===
        self.data_incoming = {}
        self.data_outgoing = None

        # === Parameters set during setup ===
        self.id = None
        self.coordinator = None
        self.clients = None



        # === Variables from config.yml
        self.input_filename = None
        self.sep = None
        self.output_filename = None

        # === Internals ===
        self.thread = None
        self.iteration = 0
        self.progress = "not started yet"
        self.local_result = None
        self.global_result = None

        # === Web status ===
        self.web_status = 'index'


        # === FCFederatedPCA instance ===
        self.svd = None
        self.step = 'pre_start'

    def handle_setup(self, client_id, master, clients):
        # This method is called once upon startup and contains information about the execution context of this instance
        self.id = client_id
        self.coordinator = master
        self.clients = clients
        print(f"Received setup: {self.id} {self.coordinator} {self.clients}", flush=True)
        if self.coordinator:
            self.svd = AggregatorFCFederatedPCA()
        else:
            self.svd = ClientFCFederatedPCA()
        # set the pointer to the first action
        self.step = self.svd.next_state()
        self.thread = threading.Thread(target=self.app_flow)
        self.thread.start()

    def handle_incoming(self, data, query):
        # This method is called when new data arrives
        print("Process incoming data....", flush=True)
        client = query.getunicode('client')
        incoming = data.read()
        # Here we use a dictionary because some information is client
        # specific
        incoming = jsonpickle.decode(incoming)
        step = incoming['step']
        print(self.data_incoming.keys())
        if step in self.data_incoming.keys():
            self.data_incoming[step][client] = incoming
        else:
            self.data_incoming[step] = {}
            self.data_incoming[step][client] = incoming


    def handle_outgoing(self):
        print("Process outgoing data...", flush=True)
        # This method is called when data is requested
        outgoing_data = self.data_outgoing
        self.data_outgoing = None
        self.status_available = False
        return outgoing_data

    def app_flow(self):
        # This method contains a state machine for the participant and coordinator instance
        while True:
            print(self.step)
            if self.step == Step.LOAD_CONFIG:
                try:
                    self.progress = "initializing..."
                    print("[CLIENT] Parsing parameter file...", flush=True)
                    if self.id is not None:  # Test is setup has happened already
                        # parse parameters
                        self.svd.parse_configuration()

                    if not self.svd.config_available:
                        self.web_status = 'setup_via_user_interface'
                    else:
                        self.svd.finalize_parameter_setup()
                        print("[CLIENT] finished parsing parameter file.", flush=True)
                except KeyError:
                    print('Error parsing parameter file: missing keys in yaml specification')
                except:
                    print('Error parsing parameter file: unknown error')

            elif self.step == Step.WAIT_FOR_PARAMS:
                wait_for = Step.LOAD_CONFIG.value
                print('CLIENT waiting for parameters '+ str(wait_for))
                if wait_for in self.data_incoming.keys() and len(self.data_incoming[wait_for]) > 0:
                    try:
                        key = list(self.data_incoming[wait_for].keys())[0]
                        incoming = self.data_incoming[wait_for][key]
                        self.data_incoming.pop(wait_for, None)
                        self.svd.set_parameters(incoming)
                    except:
                        print("Error")
                    
            elif self.step == Step.READ_DATA:
                self.progress = "read input..."
                print("[CLIENT] Read input...", flush=True)
                # Read the config file
                self.svd.read_input_files()
                # Here you could read in your input files
                print("[CLIENT] Read input finished.", flush=True)

            elif self.step == Step.INIT_POWER_ITERATION:
                try:
                    self.svd.init_random()
                    print('SVD init done')
                    self.svd.init_power_iteration()
                except:
                    print('Power iteration initialisation failed')

            elif self.step == Step.APPROXIMATE_LOCAL_PCA:
                self.svd.init_approximate()
                self.svd.init_approximate_pca()

            elif self.step == Step.AGGREGATE_SUBSPACES:
                wait_for = Step.APPROXIMATE_LOCAL_PCA.value
                print('CLIENT waiting for parameters ' + str(wait_for))
                if wait_for in self.data_incoming.keys() and len(self.data_incoming[wait_for]) == len(self.clients):
                    print("[COORDINATOR] Received data of all participants.", flush=True)
                    print("[COORDINATOR] Aggregate results...", flush=True)
                    # Decode received data of each client
                    incoming = [client_data for client_data in self.data_incoming[wait_for].values()]
                    # Empty the incoming data (important for multiple iterations)
                    self.data_incoming.pop(wait_for, None)
                    self.svd.aggregate_local_subspaces(incoming)

            elif self.step == Step.COMPUTE_G_LOCAL:
                if Step.AGGREGATE_SUBSPACES.value in self.data_incoming.keys():
                    wait_for = Step.AGGREGATE_SUBSPACES.value
                elif Step.AGGREGATE_H.value in self.data_incoming.keys():
                    wait_for = Step.AGGREGATE_H.value
                print('CLIENT waiting for parameters ' + str(wait_for))
                if wait_for in self.data_incoming.keys() and len(self.data_incoming[wait_for]) > 0:
                    print("[CLIENT] Process aggregated result from coordinator...", flush=True)
                    # Decode broadcasted data
                    key = list(self.data_incoming[wait_for].keys())[0]
                    incoming = self.data_incoming[wait_for][key]
                    # Empty incoming data
                    self.data_incoming.pop(wait_for, None)
                    try:
                        self.svd.compute_g(incoming)
                        self.silent_step = True
                    except:
                        print('G computation failed')

            elif self.step == Step.COMPUTE_H_LOCAL:
                if self.svd.federated_qr == QR.FEDERATED_QR:
                    try:
                        print('Computing H')
                        self.svd.compute_h_local_g()
                    except:
                        print('H computation failed')

            elif self.step == Step.AGGREGATE_H:
                if Step.COMPUTE_H_LOCAL.value in self.data_incoming.keys():
                    wait_for = Step.COMPUTE_H_LOCAL.value
                elif Step.UPDATE_H.value in self.data_incoming.keys():
                    wait_for = Step.UPDATE_H.value
                else:
                    wait_for = Step.INIT_POWER_ITERATION.value
                print('COORDINATOR waiting for parameters ' + str(wait_for))
                if wait_for in self.data_incoming.keys() and len(self.data_incoming[wait_for]) == len(self.clients):
                    print("[COORDINATOR] Received data of all participants.", flush=True)
                    print("[COORDINATOR] Aggregate results...", flush=True)
                    # Decode received data of each client
                    incoming = [client_data for client_data in self.data_incoming[wait_for].values()]
                    # Empty the incoming data (important for multiple iterations)
                    self.data_incoming.pop(wait_for, None)
                    try:
                        self.svd.aggregate_h(incoming)
                    except:
                        print('H aggregation failed')

            elif self.step == Step.UPDATE_H:
                if self.iteration == 0:
                    wait_for = Step.AGGREGATE_SUBSPACES.value
                else:
                    wait_for = Step.AGGREGATE_H.value
                if wait_for in self.data_incoming.keys() and len(self.data_incoming[wait_for]) > 0:
                    print("[CLIENT] Process aggregated result from coordinator...", flush=True)
                    # Decode broadcasted data
                    key = list(self.data_incoming[wait_for].keys())[0]
                    incoming = self.data_incoming[wait_for][key]
                    self.data_incoming.pop(wait_for, None)
                    self.svd.update_h(incoming)
                    self.iteration = self.iteration + 1


            elif self.step == Step.COMPUTE_LOCAL_NORM:
                if self.silent_step:
                    self.silent_step = False
                    self.svd.compute_local_eigenvector_norm()


            elif self.step == Step.COMPUTE_LOCAL_CONORM:
                wait_for = Step.AGGREGATE_NORM.value
                if wait_for in self.data_incoming.keys() and len(self.data_incoming[wait_for]) > 0:
                    print("[CLIENT] Process aggregated result from coordinator...", flush=True)
                    # Decode broadcasted data
                    key = list(self.data_incoming[wait_for].keys())[0]
                    incoming = self.data_incoming[wait_for][key]
                    # Empty incoming data
                    self.data_incoming.pop(wait_for, None)
                    try:
                        self.svd.calculate_local_vector_conorms(incoming)
                    except:
                        print('Local co-norm computation failed')

            elif self.step == Step.ORTHOGONALISE_CURRENT:
                wait_for = Step.AGGREGATE_CONORM.value
                if wait_for in self.data_incoming.keys() and len(self.data_incoming[wait_for]) > 0:
                    print("[CLIENT] Process aggregated result from coordinator...", flush=True)
                    # Decode broadcasted data
                    key = list(self.data_incoming[wait_for].keys())[0]
                    incoming = self.data_incoming[wait_for][key]
                    # Empty incoming data
                    self.data_incoming.pop(wait_for, None)
                    try:
                        self.svd.orthogonalise_current(incoming)
                        self.silent_step = True
                    except:
                        print('Orthogonalisation failed')

            elif self.step == Step.AGGREGATE_NORM:
                wait_for = Step.COMPUTE_LOCAL_NORM.value
                if wait_for in self.data_incoming.keys() and len(self.data_incoming[wait_for]) == len(self.clients):
                    print("[COORDINATOR] Received data of all participants.", flush=True)
                    print("[COORDINATOR] Aggregate results...", flush=True)
                    # Decode received data of each client
                    # the parameters are client specific
                    incoming = [client_data for client_data in self.data_incoming[wait_for].values()]
                    # Empty the incoming data (important for multiple iterations)
                    self.data_incoming.pop(wait_for, None)
                    try:
                        self.svd.aggregate_eigenvector_norms(incoming)
                    except:
                        print("Eigenvector aggregatio failed")

            elif self.step == Step.AGGREGATE_CONORM:
                wait_for = Step.COMPUTE_LOCAL_CONORM.value
                if wait_for in self.data_incoming.keys() and len(self.data_incoming[wait_for]) == len(self.clients):
                    print("[COORDINATOR] Received data of all participants.", flush=True)
                    print("[COORDINATOR] Aggregate results...", flush=True)
                    # Decode received data of each client
                    #incoming = [jsonpickle.decode(client_data) for client_data in self.data_incoming]
                    # the parameters are client specific
                    incoming = [client_data for client_data in self.data_incoming[wait_for].values()]
                    # Empty the incoming data (important for multiple iterations)
                    self.data_incoming.pop(wait_for, None)
                    try:
                        self.svd.aggregate_conorms(incoming)
                    except:
                        print('Co-norm aggregation failed')

            elif self.step == Step.NORMALISE_G:
                wait_for = Step.AGGREGATE_NORM.value
                print('CLIENT waiting for parameters ' + str(wait_for))
                if wait_for in self.data_incoming.keys() and len(self.data_incoming[wait_for]) > 0:
                    print("[CLIENT] Process aggregated result from coordinator...", flush=True)
                    # Decode broadcasted data
                    key = list(self.data_incoming[wait_for].keys())[0]
                    incoming = self.data_incoming[wait_for][key]
                    # Empty incoming data
                    self.data_incoming.pop(wait_for, None)
                    try:
                        self.svd.normalise_orthogonalised_matrix(incoming)
                    except:
                        print('G normalisation failed')

            elif self.step == Step.COMPUTE_PROJECTIONS:
                try:
                    self.svd.compute_projections()
                except:
                    print('Computation of projections failed.')

            elif self.step == Step.SAVE_PROJECTIONS:
                self.svd.save_projections()


            elif self.step == Step.SAVE_SVD:
                try:
                    self.svd.save_pca()
                except:
                    print('SVD saving failed')

            elif self.step == Step.FINALIZE:
                wait_for = Step.FINALIZE.value
                if self.coordinator:
                    if (wait_for in self.data_incoming.keys() and \
                            len(self.data_incoming[wait_for]) >= len(self.clients)-1) or len(self.clients)==1:
                        self.status_finished = True
                        self.step = Step.FINISHED
                else:
                    out = {'finished': True, 'step': Step.FINALIZE.value}
                    self.data_outgoing = jsonpickle.encode(out)
                    self.status_available = True
                    self.status_finished = True
                    self.step = Step.FINISHED

            elif self.step == Step.FINISHED:
                print('App run completed')

            else:
                print("[CLIENT] NO SUCH STATE", flush=True)


            # Dispatch data if required
            if self.svd.computation_done:
                try:
                    self.svd.computation_done = False
                    # in the svd object
                    # include the current step into the sent
                    # data object

                    if self.svd.send_data:
                        # Send data if required
                        #print(self.svd.out)
                        st = self.step.value
                        self.svd.out['step'] = st
                        self.data_outgoing = jsonpickle.encode(self.svd.out)
                        self.status_available = True
                        if self.coordinator:
                            if self.step.value in self.data_incoming.keys():
                                self.data_incoming[st][self.id] = self.svd.out
                            else:
                                self.data_incoming[st] = {}
                                self.data_incoming[st][self.id] = self.svd.out
                    else:
                        # Master just moves its local model to the inbox
                        # for easy aggregation
                        # dont encode because data is decoded upn arrival
                        if self.svd.out is not None:
                            st = self.step.value
                            self.svd.out['step'] = st
                            if self.step.value in self.data_incoming.keys():
                                self.data_incoming[st][self.id] = self.svd.out
                            else:
                                self.data_incoming[st] = {}
                                self.data_incoming[st][self.id] = self.svd.out
                    # reset the states
                    self.svd.out = None
                    self.svd.send_data = False
                    # the app orchestration status
                    #finally, increment the step
                    self.step = self.svd.next_state()
                except:
                    print('Dispatch failed')
            time.sleep(1)


logic = AppLogic()
