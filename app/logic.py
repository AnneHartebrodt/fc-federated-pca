import shutil
import threading
import time
import jsonpickle
import yaml
from app.algo import local_computation, global_aggregation
from app.Aggregator_FC_Federated_PCA import AggregatorFCFederatedPCA
from app.Client_FC_FederatedPCA import ClientFCFederatedPCA
from app.Steps import Step
from app.SVD import SVD


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
        self.data_incoming[client] = incoming

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
            if self.step == Step.LOAD_CONFIG:
                try:
                    print(self.step)
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
                except:
                    print('Error parsing parameter file!')

            elif self.step == Step.WAIT_FOR_PARAMS:
                print('CLIENT waiting for parameters')
                if len(self.data_incoming) > 0:
                    try:
                        print(self.step)
                        key = list(self.data_incoming.keys())[0]
                        incoming = jsonpickle.decode(self.data_incoming[key])
                        self.data_incoming = {}
                        self.svd.set_parameters(incoming)
                    except:
                        print("Error")
                    
            elif self.step == Step.READ_DATA:
                print(self.step)
                self.progress = "read input..."
                print("[CLIENT] Read input...", flush=True)
                # Read the config file
                self.svd.read_input_files()
                # Here you could read in your input files
                print("[CLIENT] Read input finished.", flush=True)

            elif self.step == Step.COMPUTE_LOCAL_SUMS:
                try:
                    self.svd.compute_local_sums()
                except:
                    print('Computing local sums failed')

            elif self.step == Step.COMPUTE_GLOBAL_MEANS:
                if len(self.data_incoming) == len(self.clients):
                    print(self.step)
                    print("[COORDINATOR] Received data of all participants.", flush=True)
                    print("[COORDINATOR] Aggregate results...", flush=True)
                    # Decode received data of each client
                    incoming = [jsonpickle.decode(client_data) for client_data in self.data_incoming.values()]
                    # Empty the incoming data (important for multiple iterations)
                    self.data_incoming = {}
                    try:
                        self.svd.compute_global_means(incoming)
                    except:
                        print("Aggregation error")

            elif self.step == Step.SCALE_DATA:
                if len(self.data_incoming) > 0:
                    print(self.step)
                    print("[CLIENT] Process aggregated result from coordinator...", flush=True)
                    # Decode broadcasted data
                    key = list(self.data_incoming.keys())[0]
                    incoming = jsonpickle.decode(self.data_incoming[key])
                    # Empty incoming data
                    self.data_incoming = {}
                    try:
                        self.svd.scale_data(incoming)
                    except:
                        print('scaling error')

            elif self.step == Step.COMPUTE_LOCAL_SUM_OF_SQUARES:
                try:
                    print(self.step)
                    self.svd.compute_local_sum_of_squares()
                except:
                    print('Computing local sum of squares failed')

            elif self.step == Step.AGGREGATE_SUM_OF_SQUARES:
                if len(self.data_incoming) == len(self.clients):
                    print(self.step)
                    print("[COORDINATOR] Received data of all participants.", flush=True)
                    print("[COORDINATOR] Aggregate results...", flush=True)
                    # Decode received data of each client
                    incoming = [jsonpickle.decode(client_data) for client_data in self.data_incoming.values()]
                    # Empty the incoming data (important for multiple iterations)
                    self.data_incoming = {}
                    try:
                        self.svd.compute_global_sum_of_squares(incoming)
                    except:
                        print("Aggregation error")


            elif self.step == Step.SCALE_TO_UNIT_VARIANCE:
                if len(self.data_incoming) > 0:
                    print(self.step)
                    print("[CLIENT] Process aggregated result from coordinator...", flush=True)
                    # Decode broadcasted data
                    key = list(self.data_incoming.keys())[0]
                    incoming = jsonpickle.decode(self.data_incoming[key])
                    # Empty incoming data
                    self.data_incoming = {}
                    try:
                        self.svd.scale_data_to_unit_variance(incoming)
                    except:
                        print('scaling error')

            elif self.step == Step.SAVE_SCALED_DATA:
                try:
                    print(self.step)
                    self.svd.save_scaled_data()
                except:
                    print('Saving data failed')

            elif self.step == Step.INIT_POWER_ITERATION:
                try:
                    print(self.step)
                    self.svd.pca = SVD.init_random(self.svd.tabdata, k=self.svd.k)
                    print('object created')
                    self.svd.init_power_iteration()
                except:
                    print('Power iteration initialisation failed')

            elif self.step == Step.COMPUTE_G_LOCAL:
                if len(self.data_incoming) > 0:
                    print(self.step)
                    print("[CLIENT] Process aggregated result from coordinator...", flush=True)
                    # Decode broadcasted data
                    key = list(self.data_incoming.keys())[0]
                    incoming = jsonpickle.decode(self.data_incoming[key])
                    # Empty incoming data
                    self.data_incoming = {}
                    try:
                        self.svd.compute_g(incoming)
                    except:
                        print('G computation failed')

            elif self.step == Step.COMPUTE_H_LOCAL:
                if self.svd.federated_qr:
                    print(self.step)
                    try:
                        self.svd.compute_h_local_g()
                    except:
                        print('H computation failed')
                else:
                    if len(self.data_incoming) > 0:
                        print(self.step)
                        print("[CLIENT] Process aggregated result from coordinator...", flush=True)
                        # Decode broadcasted dnerdyata
                        key = list(self.data_incoming.keys())[0]
                        incoming = jsonpickle.decode(self.data_incoming[key])
                        # Empty incoming data
                        self.data_incoming = {}
                        try:
                            self.svd.compute_h(incoming, self.id)
                        except:
                            print('H computation failed')

            elif self.step == Step.AGGREGATE_H:
                if len(self.data_incoming) == len(self.clients):
                    print(self.step)
                    print("[COORDINATOR] Received data of all participants.", flush=True)
                    print("[COORDINATOR] Aggregate results...", flush=True)
                    # Decode received data of each client
                    incoming = [jsonpickle.decode(client_data) for client_data in self.data_incoming.values()]
                    # Empty the incoming data (important for multiple iterations)
                    self.data_incoming = {}
                    try:
                        self.svd.aggregate_h(incoming)
                    except:
                        print('H aggregation failed')

            elif self.step == Step.ORTHONORMALISE_G:
                if len(self.data_incoming) == len(self.clients):
                    print(self.step)
                    print("[COORDINATOR] Received data of all participants.", flush=True)
                    print("[COORDINATOR] Aggregate results...", flush=True)
                    # Decode received data of each client
                    #incoming = [jsonpickle.decode(client_data) for client_data in self.data_incoming]
                    # the parameters are client specific
                    incoming = {}
                    print(self.data_incoming)
                    for i in self.data_incoming:
                        incoming[i] = jsonpickle.decode(self.data_incoming[i])
                    # Empty the incoming data (important for multiple iterations)
                    self.data_incoming = {}
                    try:
                        self.svd.orthonormalise_g(incoming, self.clients)
                    except:
                        print('G orthonormalisation failed')

            elif self.step == Step.WAIT_FOR_G:
                if len(self.data_incoming) > 0:
                    print(self.step)
                    print("[CLIENT] Process aggregated result from coordinator...", flush=True)
                    # Decode broadcasted data
                    key = list(self.data_incoming.keys())[0]
                    incoming = jsonpickle.decode(self.data_incoming[key])
                    # Empty incoming data
                    self.data_incoming = {}
                    try:
                        self.svd.wait_for_g(incoming, self.id)
                    except:
                        print('Problem retrieving G')

            elif self.step == Step.COMPUTE_LOCAL_NORM:
                try:
                    print(self.step)
                    print('Computing local norms')
                    self.svd.compute_local_eigenvector_norm()
                except:
                    print('Local norm computation failed')

            elif self.step == Step.COMPUTE_LOCAL_CONORM:
                if len(self.data_incoming) > 0:
                    print(self.step)
                    print("[CLIENT] Process aggregated result from coordinator...", flush=True)
                    # Decode broadcasted data
                    key = list(self.data_incoming.keys())[0]
                    incoming = jsonpickle.decode(self.data_incoming[key])
                    # Empty incoming data
                    self.data_incoming = {}
                    try:
                        self.svd.calculate_local_vector_conorms(incoming)
                    except:
                        print('Local co-norm computation failed')

            elif self.step == Step.ORTHOGONALISE_CURRENT:
                if len(self.data_incoming) > 0:
                    print(self.step)
                    print("[CLIENT] Process aggregated result from coordinator...", flush=True)
                    # Decode broadcasted data
                    key = list(self.data_incoming.keys())[0]
                    incoming = jsonpickle.decode(self.data_incoming[key])
                    # Empty incoming data
                    self.data_incoming = {}
                    try:
                        self.svd.orthogonalise_current(incoming)
                    except:
                        print('Orthogonalisation failed')

            elif self.step == Step.AGGREGATE_NORM:
                if len(self.data_incoming) == len(self.clients):
                    print(self.step)
                    print("[COORDINATOR] Received data of all participants.", flush=True)
                    print("[COORDINATOR] Aggregate results...", flush=True)
                    # Decode received data of each client
                    # the parameters are client specific
                    incoming = [jsonpickle.decode(client_data) for client_data in self.data_incoming.values()]
                    # Empty the incoming data (important for multiple iterations)
                    self.data_incoming = {}
                    try:
                        self.svd.aggregate_eigenvector_norms(incoming)
                    except:
                        print("Eigenvector aggregatio failed")

            elif self.step == Step.AGGREGATE_CONORM:

                if len(self.data_incoming) == len(self.clients):
                    print(self.step)
                    print("[COORDINATOR] Received data of all participants.", flush=True)
                    print("[COORDINATOR] Aggregate results...", flush=True)
                    # Decode received data of each client
                    #incoming = [jsonpickle.decode(client_data) for client_data in self.data_incoming]
                    # the parameters are client specific
                    incoming = [jsonpickle.decode(client_data) for client_data in self.data_incoming.values()]
                    # Empty the incoming data (important for multiple iterations)
                    self.data_incoming = {}
                    try:
                        self.svd.aggregate_conorms(incoming)
                    except:
                        print('Co-norm aggregation failed')

            elif self.step == Step.NORMALISE_G:
                if len(self.data_incoming) > 0:
                    print(self.step)
                    print("[CLIENT] Process aggregated result from coordinator...", flush=True)
                    # Decode broadcasted data
                    key = list(self.data_incoming.keys())[0]
                    incoming = jsonpickle.decode(self.data_incoming[key])
                    # Empty incoming data
                    self.data_incoming = {}
                    try:
                        self.svd.normalise_orthogonalised_matrix(incoming)
                    except:
                        print('G normalisation failed')

            elif self.step == Step.COMPUTE_PROJECTIONS:
                try:
                    print(self.step)
                    self.svd.compute_projections()
                except:
                    print('Computation of projections failed.')

            elif self.step == Step.SAVE_PROJECTIONS:
                try:
                    print(self.step)
                    self.svd.save_projections()
                except:
                    print('Saving of projections failed')

            elif self.step == Step.SHOW_RESULT:
                print('[CLIENT] Waiting for user interaction')
                self.web_status = 'show_result'

            elif self.step == Step.SAVE_SVD:
                try:
                    print(self.step)
                    self.svd.save_pca()
                except:
                    print('SVD saving failed')

            elif self.step == Step.FINALIZE:
                print(self.step)
                if self.coordinator:
                    if len(self.data_incoming) == (len(self.clients)-1):
                        self.status_finished = True
                        self.step = Step.FINISHED
                else:
                    self.data_outgoing = jsonpickle.encode(True)
                    self.status_available = True
                    time.sleep(3)
                    self.status_finished = True
                    self.step = Step.FINISHED

            elif self.step == Step.FINISHED:
                print('App run completed')

            else:
                print("[CLIENT] NO SUCH STATE", flush=True)


            # Dispatch data if required
            if self.svd.computation_done:
                self.svd.computation_done = False
                # in the svd object
                if self.svd.send_data:
                    # Send data if required
                    self.data_outgoing = jsonpickle.encode(self.svd.out)
                    self.status_available = True
                    if self.coordinator:
                        self.data_incoming[self.id] = jsonpickle.encode(self.svd.out)
                else:
                    # Master just moves its local model to the inbox
                    # for easy aggregation
                    if self.svd.out is not None:
                        self.data_incoming[self.id] = jsonpickle.encode(self.svd.out)
                # reset the states
                self.svd.out = None
                self.svd.send_data = False
                # the app orchestration status
                #finally, increment the step
                self.step = self.svd.next_state()
            time.sleep(1)


logic = AppLogic()
