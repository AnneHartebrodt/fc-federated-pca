import shutil
import threading
import time
import jsonpickle
import yaml
from app.algo import local_computation, global_aggregation
from app.Aggregator_FC_Federated_PCA import AggregatorFCFederatedPCA
from app.Client_FC_FederatedPCA import ClientFCFederatedPCA
from app.Steps import Step

class AppLogic:

    def __init__(self):
        # === Status of this app instance ===

        # Indicates whether there is data to share, if True make sure self.data_out is available
        self.status_available = False

        # Will stop execution when True
        self.status_finished = False

        # === Data ===
        self.data_incoming = []
        self.data_outgoing = None

        # === Parameters set during setup ===
        self.id = None
        self.coordinator = None
        self.clients = None



        # === Variables from config.yml
        self.config_available = True
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

    def handle_incoming(self, data):
        # This method is called when new data arrives
        print("Process incoming data....", flush=True)
        print(self.data_incoming)
        incoming = data.read()
        print("[CLIENT] incoming: "+str(incoming))
        self.data_incoming.append(incoming)

    def handle_outgoing(self):
        print("Process outgoing data...", flush=True)
        # This method is called when data is requested
        outgoing_data = self.data_outgoing
        print('[API] out'+ str(outgoing_data))
        self.data_outgoing = None
        self.status_available = False
        return outgoing_data

    def app_flow(self):
        # This method contains a state machine for the participant and coordinator instance

        # === States ===
        state_initializing = 1
        state_read_input_files = 2
        state_local_computation = 3
        state_wait_for_aggregation = 4
        state_global_aggregation = 5
        state_finish = 6

        # Initial state
        state = 7
        while True:
            print(self.step)
            if self.step == Step.LOAD_CONFIG:
                self.progress = "initializing..."
                print("[CLIENT] Parsing parameter file...", flush=True)
                if self.id is not None:  # Test is setup has happened already
                    # parse parameters
                    self.svd.parse_configuration()
                    self.svd.finalize_parameter_setup()
                print("[CLIENT] finished parsing parameter file.", flush=True)

            elif self.step == Step.WAIT_FOR_PARAMS:
                print('CLIENT waiting for parameters')
                if len(self.data_incoming) > 0:
                    try:
                        print(self.data_incoming)
                        incoming = jsonpickle.decode(self.data_incoming[0])
                        self.data_incoming = []
                        print(incoming)
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

            elif self.step == Step.COMPUTE_LOCAL_SUMS:
                try:
                    self.svd.compute_local_sums()
                except:
                    print('Computing local sums failed')

            elif self.step == Step.COMPUTE_GLOBAL_MEANS:
                if len(self.data_incoming) == len(self.clients):
                    print("[COORDINATOR] Received data of all participants.", flush=True)
                    print("[COORDINATOR] Aggregate results...", flush=True)
                    # Decode received data of each client
                    incoming = [jsonpickle.decode(client_data) for client_data in self.data_incoming]
                    # Empty the incoming data (important for multiple iterations)
                    self.data_incoming = []
                    try:
                        self.svd.compute_global_means(incoming)
                    except:
                        print("Aggregation error")

            elif self.step == Step.SCALE_DATA:
                if len(self.data_incoming) > 0:
                    print("[CLIENT] Process aggregated result from coordinator...", flush=True)
                    # Decode broadcasted data
                    incoming = jsonpickle.decode(self.data_incoming[0])
                    # Empty incoming data
                    self.data_incoming = []
                    try:
                        self.svd.scale_data(incoming)
                    except:
                        print('scaling error')

            elif self.step == Step.COMPUTE_LOCAL_SUM_OF_SQUARES:
                try:
                    self.svd.compute_local_sum_of_squares()
                except:
                    print('Computing local sum of squares failed')

            elif self.step == Step.AGGREGATE_SUM_OF_SQUARES:
                if len(self.data_incoming) == len(self.clients):
                    print("[COORDINATOR] Received data of all participants.", flush=True)
                    print("[COORDINATOR] Aggregate results...", flush=True)
                    # Decode received data of each client
                    incoming = [jsonpickle.decode(client_data) for client_data in self.data_incoming]
                    # Empty the incoming data (important for multiple iterations)
                    self.data_incoming = []
                    try:
                        self.svd.compute_global_sum_of_squares(incoming)
                    except:
                        print("Aggregation error")


            elif self.step == Step.SCALE_TO_UNIT_VARIANCE:
                if len(self.data_incoming) > 0:
                    print("[CLIENT] Process aggregated result from coordinator...", flush=True)
                    # Decode broadcasted data
                    incoming = jsonpickle.decode(self.data_incoming[0])
                    # Empty incoming data
                    self.data_incoming = []
                    try:
                        self.svd.scale_data_to_unit_variance(incoming)
                    except:
                        print('scaling error')

            elif self.step == Step.FINALIZE:
                self.svd.save_scaled_data()
                self.status_finished = True

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
                        self.data_incoming.append(jsonpickle.encode(self.svd.out))
                else:
                    # Master just moves its local model to the inbox
                    # for easy aggregation
                    if self.svd.out is not None:
                        self.data_incoming.append(jsonpickle.encode(self.svd.out))
                # reset the states
                self.svd.out = None
                self.svd.send_data = False
                # the app orchestration status
                #finally, increment the step
                self.step = self.svd.next_state()
            time.sleep(1)


logic = AppLogic()
