import shutil
import threading
import time
import jsonpickle
import jsonpickle.ext.numpy as jsonpickle_numpy
jsonpickle_numpy.register_handlers()
from app.Aggregator_FC_Federated_PCA import AggregatorFCFederatedPCA
from app.Client_FC_FederatedPCA import ClientFCFederatedPCA
from app.Steps import Step
from app.algo_params import QR, PCA_TYPE
from app.config import FCConfig
import os.path as op
from app.params import OUTPUT_DIR
import numpy as np
import pandas as pd
from app.COParams import COParams


class AppLogic:

    def __init__(self):
        # === Status of this app instance ===

        # Indicates whether there is data to share, if True make sure self.data_out is available
        self.status_available = False

        #
        self.use_smpc = False
        self.status_smpc = False
        self.exponent = 15
        self.shards = 1
        # Will stop execution when True
        self.status_finished = False
        self.finish_count=0

        # === Data ===
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
        self.message = 'Starting'
        self.workflow_state = 'running'
        self.local_result = None
        self.global_result = None
        self.progress = 0.0

        # === Web status ===
        self.web_status = 'index'



        # === FCFederatedPCA instance ===
        self.svd = None

        self.communication_logger = []
        self.start_time = 0

    def handle_setup(self, client_id, master, clients):
        # This method is called once upon startup and contains information about the execution context of this instance
        self.id = client_id
        self.coordinator = master
        self.clients = clients
        self.shards = len(self.clients)
        print(f"Received setup: {self.id} {self.coordinator} {self.clients}", flush=True)
        self.configure()
        print('Test')
        self.start_time = time.monotonic()
        self.svd = {}
        print('Test')
        # batch config loops over the files
        if self.config.batch:
            print('batch mode')
            print(self.config.directories)
            i = 0
            for d in self.config.directories:

                if self.config.train_test:
                    l = ['train', 'test']
                else:
                    l = ['']
                for t in l:
                    if self.coordinator:
                        self.svd[i] = AggregatorFCFederatedPCA()
                    else:
                        self.svd[i] = ClientFCFederatedPCA()
                    print('Object created')
                    self.svd[i].step = Step.LOAD_CONFIG
                    self.svd[i].copy_configuration(self.config, d, t)
                    print('Configuration copied')
                    self.svd[i].finalize_parameter_setup()
                    print('Setup finalized')
                    i = i + 1

        else:
            print('single mode')
            if self.coordinator:
                self.svd[0] = AggregatorFCFederatedPCA()
            else:
                self.svd[0] = ClientFCFederatedPCA()
            print('Object created')
            self.svd[0].step = Step.LOAD_CONFIG
            self.svd[0].copy_configuration(self.config, '', '')
            print('Configuartion copied')
            self.svd[0].finalize_parameter_setup()

        # set the pointer to the first action
        for i in range(len(self.svd)):
            self.svd[i].step = self.svd[i].next_state()

        print('start flow')
        self.use_smpc = self.svd[0].use_smpc
        print(self.use_smpc)
        print(self.svd[0].use_smpc)
        self.thread = threading.Thread(target=self.app_flow)
        self.thread.start()

    def handle_incoming(self, data, query, content_length):
        # This method is called when new data arrives
        print("Process incoming data....", flush=True)
        client = query.getunicode('client')

        print('client: '+str(client))
        incoming = data.read()
        print('Recieved data length:')
        self.communication_logger.append(content_length)
        # Here we use a dictionary because some information is client
        # specific
        print(incoming)
        incoming = jsonpickle.decode(incoming)
        print(incoming)
        for i in incoming.keys():
            j = int(i)
            try:
                step = incoming[i][COParams.STEP.n]
            except:
                #This works around the problem, that when using SMPC you can only send smpc-able parameters
                step = self.aux_step_mapper(incoming[i].keys())
            if step in self.svd[j].data_incoming.keys():
                self.svd[j].data_incoming[step][client] = incoming[i]
            else:
                print('Step'+str(step))
                self.svd[j].data_incoming[step] = {}
                self.svd[j].data_incoming[step][client] = incoming[i]
        print("Process incoming data.... DONE!", flush=True)

    def aux_step_mapper(self, keys):
        for k in keys:
            if COParams.to_step(k) is not None:
                return COParams.to_step(k)

    def configure(self):
        print("[CLIENT] Parsing parameter file...", flush=True)
        if self.id is not None:  # Test is setup has happened already
            # parse parameters
            self.config = FCConfig()
            print('Config created')
            self.config.parse_configuration()
            print("[CLIENT] finished parsing parameter file.", flush=True)

    def shutdown(self):
        log_file = op.join(OUTPUT_DIR, 'logs.txt')
        end = time.monotonic()
        with open(log_file, 'w') as handle:
            handle.write('start\t'+str(self.start_time)+'\n')
            handle.write('end\t' + str(end)+'\n')
            handle.write('elapsed\t' + str(end-self.start_time)+'\n')
            handle.write('communication rounds\t' + str(self.iteration)+'\n')
            handle.write('packages sent\t' + str(len(self.communication_logger))+'\n')
            handle.write('average package size\t' + str(np.mean(self.communication_logger))+'\n')
            handle.write('max package size\t' + str(np.max(self.communication_logger))+'\n')
            handle.write('min package size\t' + str(np.min(self.communication_logger))+'\n')
        pd.DataFrame(self.communication_logger).to_csv(op.join(OUTPUT_DIR, 'communication.txt'), header=False, index=False, sep='\t')






    def handle_outgoing(self):
        print("Process outgoing data...", flush=True)
        # This method is called when data is requested
        outgoing_data = self.data_outgoing
        self.data_outgoing = None
        self.status_available = False
        self.status_smpc = False
        return outgoing_data

    def app_flow(self):
        # This method contains a state machine for the participant and coordinator instance
        outgoing_dict = {}
        smpc_outgoing_dict = {}
        while True:
            self.progress = self.svd[0].progress
            self.message = self.svd[0].step.step
            for i in range(len(self.svd)):
                print("Current step " + str(self.svd[i].step))
                if self.svd[i].step == Step.WAIT_FOR_PARAMS:
                    wait_for = Step.LOAD_CONFIG
                    print('CLIENT waiting for parameters ' + str(wait_for))
                    if wait_for in self.svd[i].data_incoming.keys() and len(self.svd[i].data_incoming[wait_for]) > 0:
                        try:
                            key = list(self.svd[i].data_incoming[wait_for].keys())[0]
                            incoming = self.svd[i].data_incoming[wait_for][key]
                            self.svd[i].data_incoming.pop(wait_for, None)
                            self.svd[i].set_parameters(incoming)
                        except Exception as e:

                            print("Error loading configuration")
                            print(e)
                        
                elif self.svd[i].step == Step.READ_DATA:
                    wait_for = Step.WAIT_FOR_PARAMS
                    print("[CLIENT] Read input...", flush=True)
                    self.svd[i].read_input_files()
                    self.svd[i].data_incoming.pop(wait_for, None)
                    print("[CLIENT] Read input finished.", flush=True)
    
                elif self.svd[i].step == Step.INIT_POWER_ITERATION:
                    self.iteration = self.iteration + 1
                    self.svd[i].init_random()
                    self.svd[i].init_power_iteration()
    
                elif self.svd[i].step == Step.APPROXIMATE_LOCAL_PCA:
                    self.svd[i].init_approximate()
                    self.svd[i].init_approximate_pca()

                elif self.svd[i].step == Step.COMPUTE_COVARIANCE:
                    self.svd[i].compute_covariance()

                elif self.svd[i].step == Step.COMPUTE_QR:
                    self.svd[i].compute_qr()

                elif self.svd[i].step == Step.AGGREGATE_QR:
                    wait_for = Step.COMPUTE_QR
                    print('CLIENT waiting for parameters ' + str(wait_for) + " "+str(len(self.clients)))
                    if wait_for in self.svd[i].data_incoming.keys() and len(self.svd[i].data_incoming[wait_for]) == len(
                            self.clients):
                        print("[COORDINATOR] Received data of all participants.", flush=True)
                        print("[COORDINATOR] Aggregate results...", flush=True)
                        # Decode received data of each client
                        incoming = [client_data for client_data in self.svd[i].data_incoming[wait_for].values()]
                        # Empty the incoming data (important for multiple iterations)
                        self.svd[i].aggregate_qr(incoming)


                elif self.svd[i].step == Step.AGGREGATE_SUBSPACES:
                    wait_for = Step.APPROXIMATE_LOCAL_PCA
                    print('CLIENT waiting for parameters ' + str(wait_for))
                    # key must be available
                    # if not smpc then every client has sent data
                    # if smpc 1 client has sent the aggregate
                    if wait_for in self.svd[i].data_incoming.keys() and \
                            len(self.svd[i].data_incoming[wait_for]) == len(self.clients):
                        print("[COORDINATOR] Received data of all participants.", flush=True)
                        print("[COORDINATOR] Aggregate results...", flush=True)
                        # Decode received data of each client
                        incoming = [client_data for client_data in self.svd[i].data_incoming[wait_for].values()]
                        # Empty the incoming data (important for multiple iterations)
                        self.svd[i].data_incoming.pop(wait_for, None)
                        self.svd[i].aggregate_local_subspaces(incoming)

                elif self.svd[i].step == Step.AGGREGATE_COVARIANCE:
                    wait_for = Step.COMPUTE_COVARIANCE
                    print('CLIENT waiting for parameters ' + str(wait_for))

                    # key must be available
                    # if not smpc then every client has sent data
                    # if smpc 1 client has sent the aggregate
                    if wait_for in self.svd[i].data_incoming.keys() and \
                            (len(self.svd[i].data_incoming[wait_for]) == len(self.clients) or
                                    len(self.svd[i].data_incoming[wait_for]) == 1 and self.use_smpc):
                        print("[COORDINATOR] Received data of all participants.", flush=True)
                        print("[COORDINATOR] Aggregate results...", flush=True)
                        # Decode received data of each client
                        incoming = [client_data for client_data in self.svd[i].data_incoming[wait_for].values()]
                        # Empty the incoming data (important for multiple iterations)
                        self.svd[i].data_incoming.pop(wait_for, None)
                        self.svd[i].aggregate_local_subspaces(incoming)


                elif self.svd[i].step == Step.COMPUTE_G_LOCAL:
                    if Step.AGGREGATE_SUBSPACES in self.svd[i].data_incoming.keys():
                        wait_for = Step.AGGREGATE_SUBSPACES
                    elif Step.AGGREGATE_H in self.svd[i].data_incoming.keys():
                        wait_for = Step.AGGREGATE_H
                    elif Step.INIT_POWER_ITERATION in self.svd[i].data_incoming.keys():
                        wait_for = Step.INIT_POWER_ITERATION
                    print('CLIENT waiting for parameters ' + str(wait_for))
                    if wait_for in self.svd[i].data_incoming.keys() and len(self.svd[i].data_incoming[wait_for]) > 0:
                        print("[CLIENT] Process aggregated result from coordinator...", flush=True)
                        # Decode broadcasted data
                        key = list(self.svd[i].data_incoming[wait_for].keys())[0]
                        incoming = self.svd[i].data_incoming[wait_for][key]
                        # Empty incoming data
                        self.svd[i].data_incoming.pop(wait_for, None)
                        try:
                            self.svd[i].compute_g(incoming)
                            self.svd[i].silent_step = True
                        except:
                            print('G computation failed')
    
                elif self.svd[i].step == Step.COMPUTE_H_LOCAL:
                    if self.svd[i].federated_qr == QR.FEDERATED_QR:
                        try:
                            print('Computing H')
                            self.svd[i].compute_h_local_g()
                        except Exception as e:
                            print('H computation failed')
    
                elif self.svd[i].step == Step.AGGREGATE_H:
                    if Step.COMPUTE_H_LOCAL in self.svd[i].data_incoming.keys():
                        wait_for = Step.COMPUTE_H_LOCAL
                    elif Step.UPDATE_H in self.svd[i].data_incoming.keys():
                        wait_for = Step.UPDATE_H
                    else:
                        wait_for = Step.INIT_POWER_ITERATION
                    #print('COORDINATOR waiting for parameters ' + str(wait_for) + 'Recieved '+str(len(self.svd[i].data_incoming[wait_for])))
                    if wait_for in self.svd[i].data_incoming.keys() and \
                            (len(self.svd[i].data_incoming[wait_for]) == len(self.clients) or
                             len(self.svd[i].data_incoming[wait_for]) == 1 and self.use_smpc):
                        print("[COORDINATOR] Received data of all participants.", flush=True)
                        print("[COORDINATOR] Aggregate results...", flush=True)
                        try:
                            # Decode received data of each client
                            incoming = [client_data for client_data in self.svd[i].data_incoming[wait_for].values()]
                            # Empty the incoming data (important for multiple iterations)
                            self.svd[i].data_incoming.pop(wait_for, None)
                            self.svd[i].aggregate_h(incoming)
                        except Exception as e:
                            print('H aggregation failed')
                            print(e)
    
                elif self.svd[i].step == Step.UPDATE_H:
                    if Step.AGGREGATE_SUBSPACES in self.svd[i].data_incoming.keys():
                        wait_for = Step.AGGREGATE_SUBSPACES
                    else:
                        wait_for = Step.AGGREGATE_H
                    print('CLIENT waiting for parameters ' + str(wait_for))
                    if wait_for in self.svd[i].data_incoming.keys() and len(self.svd[i].data_incoming[wait_for]) > 0:
                        print("[CLIENT] Process aggregated result from coordinator...", flush=True)
                        # Decode broadcasted data
                        key = list(self.svd[i].data_incoming[wait_for].keys())[0]
                        incoming = self.svd[i].data_incoming[wait_for][key]
                        self.svd[i].data_incoming.pop(wait_for, None)
                        self.svd[i].update_h(incoming)

    
    
                elif self.svd[i].step == Step.COMPUTE_LOCAL_NORM:
                    if self.svd[i].silent_step:
                        self.svd[i].silent_step = False
                        self.svd[i].compute_local_eigenvector_norm()
    
    
                elif self.svd[i].step == Step.COMPUTE_LOCAL_CONORM:
                    wait_for = Step.AGGREGATE_NORM
                    if wait_for in self.svd[i].data_incoming.keys() and len(self.svd[i].data_incoming[wait_for]) > 0:
                        print("[CLIENT] Process aggregated result from coordinator...", flush=True)
                        # Decode broadcasted data
                        key = list(self.svd[i].data_incoming[wait_for].keys())[0]
                        incoming = self.svd[i].data_incoming[wait_for][key]
                        # Empty incoming data
                        self.svd[i].data_incoming.pop(wait_for, None)
                        self.svd[i].calculate_local_vector_conorms(incoming)

    
                elif self.svd[i].step == Step.ORTHOGONALISE_CURRENT:
                    wait_for = Step.AGGREGATE_CONORM
                    if wait_for in self.svd[i].data_incoming.keys() and len(self.svd[i].data_incoming[wait_for]) > 0:
                        print("[CLIENT] Process aggregated result from coordinator...", flush=True)
                        # Decode broadcasted data
                        key = list(self.svd[i].data_incoming[wait_for].keys())[0]
                        incoming = self.svd[i].data_incoming[wait_for][key]
                        # Empty incoming data
                        self.svd[i].data_incoming.pop(wait_for, None)

                        self.svd[i].orthogonalise_current(incoming)
                        self.svd[i].silent_step = True
    
                elif self.svd[i].step == Step.AGGREGATE_NORM:
                    wait_for = Step.COMPUTE_LOCAL_NORM
                    if wait_for in self.svd[i].data_incoming.keys() and len(self.svd[i].data_incoming[wait_for]) == len(self.clients):
                        print("[COORDINATOR] Received data of all participants.", flush=True)
                        print("[COORDINATOR] Aggregate results...", flush=True)
                        # Decode received data of each client
                        # the parameters are client specific
                        incoming = [client_data for client_data in self.svd[i].data_incoming[wait_for].values()]
                        # Empty the incoming data (important for multiple iterations)
                        self.svd[i].data_incoming.pop(wait_for, None)
                        self.svd[i].aggregate_eigenvector_norms(incoming)
    
                elif self.svd[i].step == Step.AGGREGATE_CONORM:
                    wait_for = Step.COMPUTE_LOCAL_CONORM
                    if wait_for in self.svd[i].data_incoming.keys() and len(self.svd[i].data_incoming[wait_for]) == len(self.clients):
                        print("[COORDINATOR] Received data of all participants.", flush=True)
                        print("[COORDINATOR] Aggregate results...", flush=True)
                        incoming = [client_data for client_data in self.svd[i].data_incoming[wait_for].values()]
                        # Empty the incoming data (important for multiple iterations)
                        self.svd[i].data_incoming.pop(wait_for, None)
                        try:
                            self.svd[i].aggregate_conorms(incoming)
                        except:
                            print('Co-norm aggregation failed')
    
                elif self.svd[i].step == Step.NORMALISE_G:
                    wait_for = Step.AGGREGATE_NORM
                    print('CLIENT waiting for parameters ' + str(wait_for))
                    if wait_for in self.svd[i].data_incoming.keys() and len(self.svd[i].data_incoming[wait_for]) > 0:
                        print("[CLIENT] Process aggregated result from coordinator...", flush=True)
                        # Decode broadcasted data
                        key = list(self.svd[i].data_incoming[wait_for].keys())[0]
                        incoming = self.svd[i].data_incoming[wait_for][key]
                        # Empty incoming data
                        self.svd[i].data_incoming.pop(wait_for, None)
                        try:
                            self.svd[i].normalise_orthogonalised_matrix(incoming)
                        except:
                            print('G normalisation failed')
    
                elif self.svd[i].step == Step.COMPUTE_PROJECTIONS:
                    try:
                        self.svd[i].compute_projections()
                    except:
                        print('Computation of projections failed.')
    
                elif self.svd[i].step == Step.SAVE_PROJECTIONS:
                    self.svd[i].save_projections()
    
    
                elif self.svd[i].step == Step.SAVE_SVD:
                    if self.svd[i].algorithm in [PCA_TYPE.APPROXIMATE,  PCA_TYPE.COVARIANCE, PCA_TYPE.QR_PCA]:
                        if self.svd[i].algorithm == PCA_TYPE.APPROXIMATE and self.use_smpc:
                            wait_for = Step.AGGREGATE_COVARIANCE
                        elif self.svd[i].algorithm == PCA_TYPE.APPROXIMATE:
                            wait_for = Step.AGGREGATE_SUBSPACES
                        elif self.svd[i].algorithm == PCA_TYPE.COVARIANCE:
                            wait_for = Step.AGGREGATE_COVARIANCE
                        elif self.svd[i].algorithm == PCA_TYPE.QR_PCA:
                            wait_for = Step.AGGREGATE_QR
                    #else:
                    #    wait_for = Step.AGGREGATE_H
                        print('CLIENT waiting for parameters ' + str(wait_for))
                        # Data (H matrix) needs to be updated from the server
                        if wait_for in self.svd[i].data_incoming.keys() and len(self.svd[i].data_incoming[wait_for]) > 0:
                            print("[CLIENT] Process aggregated result from coordinator...", flush=True)
                            # Decode broadcasted data
                            key = list(self.svd[i].data_incoming[wait_for].keys())[0]
                            incoming = self.svd[i].data_incoming[wait_for][key]
                            # Empty incoming data
                            self.svd[i].data_incoming.pop(wait_for, None)
                            self.svd[i].update_and_save_pca(incoming)

                 #Data is available already
                    else:
                        self.svd[i].save_pca()


    
                elif self.svd[i].step == Step.FINALIZE:
                    wait_for = Step.FINALIZE
                    if self.coordinator:
                        print('CLIENT waiting for parameters ' + str(wait_for))
                        if (wait_for in self.svd[i].data_incoming.keys() and \
                                len(self.svd[i].data_incoming[wait_for]) >= len(self.clients)-1) or len(self.clients)==1:
                            self.shutdown()
                            self.svd[i].progress = 1.0
                            self.finish_count = self.finish_count + 1
                            self.svd[i].step = Step.FINISHED
                    else:
                        self.shutdown()
                        self.svd[i].out = {COParams.FINISHED.n: True, COParams.STEP.n: Step.FINALIZE}
                        self.svd[i].send_data = True
                        self.svd[i].computation_done = True
                        self.svd[i].progress = 1.0
                        self.svd[i].step_queue = self.svd[i].step_queue + [Step.FINISHED]

                elif self.svd[i].step == Step.FINISHED:
                    # Wait for all clients to be finished.
                    if self.finish_count == len(self.svd):
                        print('SETTING TO FINISHED')
                        time.sleep(3)
                        self.status_finished = True
                    print('App run completed')
                else:
                    print("[CLIENT] NO SUCH STATE", flush=True)


            for i in range(len(self.svd)):
                # Dispatch data if required
                if self.svd[i].computation_done:

                    self.svd[i].computation_done = False
                    # in the svd object
                    # include the current step into the sent
                    # data object

                    if self.svd[i].send_data:
                        # Send data if required
                        #print(self.svd[i].out)

                        st = self.svd[i].step
                        self.svd[i].out[COParams.STEP.n] = st

                        if self.use_smpc:
                            # Split the params
                            for key in self.svd[i].out.keys():
                                if key is not COParams.STEP.n:
                                    if COParams.from_str(key).smpc:
                                        if i not in smpc_outgoing_dict.keys():
                                            smpc_outgoing_dict[i] = {}
                                        #if COParams.STEP.n not in smpc_outgoing_dict[i].keys():
                                            #smpc_outgoing_dict[i] = {COParams.STEP.n: st}
                                        if isinstance(self.svd[i].out[key], np.ndarray):
                                            smpc_outgoing_dict[i][key] = self.svd[i].out[key].tolist()
                                        else:
                                            smpc_outgoing_dict[i][key] = self.svd[i].out[key]
                                    else:
                                        if i not in outgoing_dict.keys():
                                            outgoing_dict[i] = {}
                                        if COParams.STEP.n not in outgoing_dict[i].keys():
                                            outgoing_dict[i] = {COParams.STEP.n: st}
                                        outgoing_dict[i][key] = self.svd[i].out[key]
                        else:
                            print('outgoing data')
                            outgoing_dict[i] = self.svd[i].out

                        print(outgoing_dict)
                        print('SMPC OUTgoing')
                        print(smpc_outgoing_dict)

                        # move data to inbox, create key if not available
                        # Master just moves its local model to the inbox
                        # for easy aggregation
                        # dont encode because data is decoded upn arrival

                        # if smpc is used then the coordinator actually sends data
                        if self.coordinator and outgoing_dict!={}:
                            print('Is this dead code?')
                            if self.svd[i].step in self.svd[i].data_incoming.keys():
                                self.svd[i].data_incoming[st][self.id] = outgoing_dict[i]
                            else:
                                self.svd[i].data_incoming[st] = {}
                                #changed
                                self.svd[i].data_incoming[st][self.id] = outgoing_dict[i]
                    else:
                        print('Move data to inbox')
                        # Don't send data, just move to inbox.
                        if self.svd[i].out is not None:
                            st = self.svd[i].step
                            self.svd[i].out[COParams.STEP.n] = st
                            if self.svd[i].step in self.svd[i].data_incoming.keys():
                                self.svd[i].data_incoming[st][self.id] = self.svd[i].out
                            else:
                                self.svd[i].data_incoming[st] = {}
                                self.svd[i].data_incoming[st][self.id] = self.svd[i].out
                    # reset the states

                    self.svd[i].out = None
                    self.svd[i].send_data = False
                    # the app orchestration status
                    #finally, increment the step
                    self.svd[i].step = self.svd[i].next_state()


            if outgoing_dict != {}:
                # Dispatch and delete if object empty. Otherwise wait
                # until dispatched to add new object
                if self.data_outgoing == None:
                        self.data_outgoing = jsonpickle.encode(outgoing_dict)
                        self.iteration = self.iteration + 1
                        self.status_available = True
                        outgoing_dict = {}

            elif smpc_outgoing_dict != {}:
                print('SMPC=++++++++++++++=SMPC')
                if self.data_outgoing == None:
                        self.data_outgoing = jsonpickle.encode(smpc_outgoing_dict)
                        self.iteration = self.iteration + 1
                        self.status_available = True
                        self.status_smpc = True
                        smpc_outgoing_dict = {}


            time.sleep(1)


logic = AppLogic()
