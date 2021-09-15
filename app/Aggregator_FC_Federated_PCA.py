from app.FC_Federated_PCA import FCFederatedPCA
import  numpy as np
from app.Steps import Step
import scipy as sc
import scipy.linalg as la
from app.PCA.shared_functions import eigenvector_convergence_checker
from app.QR_params import QR
import app.PCA.shared_functions as sh

class AggregatorFCFederatedPCA(FCFederatedPCA):
    def __init__(self):
        self.dummy = None
        self.coordinator = True
        FCFederatedPCA.__init__(self)

    def finalize_parameter_setup(self):
        self.step_queue = self.step_queue + [Step.WAIT_FOR_PARAMS,
                                             Step.READ_DATA]
        if self.algorithm == 'approximate_pca':
            self.step_queue = self.step_queue + [Step.APPROXIMATE_LOCAL_PCA,
                                                 Step.AGGREGATE_SUBSPACES,
                                                 Step.UPDATE_H]
        elif self.algorithm == 'power_iteration':
            if self.init_method == 'approximate_pca':
                self.step_queue = self.step_queue + [Step.APPROXIMATE_LOCAL_PCA,
                                                     Step.AGGREGATE_SUBSPACES]
            else:
                self.step_queue = self.step_queue + [Step.INIT_POWER_ITERATION,
                                                     Step.AGGREGATE_H]

            if self.federated_qr == QR.NO_QR:
                self.step_queue = self.step_queue + [Step.UPDATE_H]
            else:
                self.step_queue = self.step_queue + [Step.COMPUTE_G_LOCAL]
        else:
            self.step_queue = [Step.FINALIZE]

        # No user interaction required, set available to true
        # master still sends configuration to all clients.
        self.out = {'pcs': self.k}

        self.send_data = True
        self.computation_done = True
        print('[API] [COORDINATOR] /setup config done!')



    def compute_h(self, incoming, client_id):
        # this is the case for federated PCA and the first iteration
        # of centralised PCA
        # Compute dot product of data and G_i
        print('Computing H locally')
        self.pca.G = incoming['g_matrices'][client_id]
        self.pca.S = incoming['eigenvalues']
        self.pca.H = np.dot(self.tabdata.scaled, self.pca.G)
        print('Done!!!')
        self.out = {'local_h': self.pca.H}
        self.computation_done = True
        self.send_data = False
        return True

    def compute_h_local_g(self):
        # this is the case for federated PCA and the first iteration
        # of centralised PCA
        print('Compute H')
        self.pca.H = np.dot(self.tabdata.scaled, self.pca.G)
        self.out = {'local_h': self.pca.H}
        self.computation_done = True
        self.send_data = False
        return True

    def queue_qr(self):
            self.step_queue = self.step_queue + [Step.COMPUTE_LOCAL_NORM,
                                                 Step.AGGREGATE_NORM,
                                                 Step.COMPUTE_LOCAL_CONORM,
                                                 Step.AGGREGATE_CONORM,
                                                 Step.ORTHOGONALISE_CURRENT] * (self.k - 1) +\
                                                [Step.COMPUTE_LOCAL_NORM,
                                                 Step.AGGREGATE_NORM,
                                                 Step.NORMALISE_G]

    def compute_g(self, incoming):
        self.pca.H = incoming['h_global']
        self.converged = incoming['converged']

        self.pca.G = np.dot(self.tabdata.scaled.T, self.pca.H)

        if self.federated_qr == QR.FEDERATED_QR:
            self.queue_qr()
            # send local norms
            if self.converged:
                self.queue_shutdown()
            else:
                self.step_queue = self.step_queue + [Step.COMPUTE_H_LOCAL, Step.AGGREGATE_H, Step.COMPUTE_G_LOCAL]

        # next local step is to follow!
        self.computation_done = True
        self.send_data = False
        print(self.step_queue)
        return True

    def update_h(self, incoming):

        # First, update the local G estimate
        self.pca.G = np.dot(self.tabdata.scaled.T, incoming['h_global'])

        # Then check for convergence.
        self.converged = incoming['converged']
        if self.converged:
            self.queue_shutdown()
        else:
            self.step_queue = self.step_queue + [Step.AGGREGATE_H, Step.UPDATE_H]

        # If convergence not reached, update H and go on
        self.pca.H = np.dot(self.tabdata.scaled, self.pca.G)
        self.out = {'local_h': self.pca.H}
        self.computation_done = True
        self.send_data = False
        return True



    def aggregate_h(self, incoming):
        '''
        This step adds up the H matrices (nr_SNPs x target dimension) matrices to
        achieve a global H matrix
        :param parameters_from_clients: The local H matrices
        :return: Global H matrix to be sent to the client
        '''

        print("Adding up H matrices from clients ...")
        global_HI_matrix = np.zeros(self.pca.H.shape)
        for m in incoming:
            global_HI_matrix += m['local_h']
        print('H matrices added up')
        global_HI_matrix, R = la.qr(global_HI_matrix, mode='economic')
        self.iteration_counter = self.iteration_counter + 1
        print(self.iteration_counter)
        # The previous H matrix is stored in the global variable
        print('orthonormalised')
        print(self.epsilon)
        converged, deltas = eigenvector_convergence_checker(global_HI_matrix, self.pca.previous_h, tolerance=self.epsilon)
        print(converged)
        if self.iteration_counter == self.max_iterations or converged:
            self.converged = True
            print('CONVERGED')
        out = {'h_global': global_HI_matrix, 'converged': self.converged}
        self.out = out
        self.send_data = True
        self.computation_done = True
        return True

    def init_power_iteration(self):
        self.iteration_counter = 0
        self.converged = False
        print(self.pca.G.shape)
        print(self.tabdata.scaled.shape)
        self.pca.previous_h = self.pca.H
        self.pca.H = np.dot(self.tabdata.scaled, self.pca.G)
        self.out = {'local_h': self.pca.H}
        if self.federated_qr == QR.FEDERATED_QR:
            self.init_federated_qr()
        self.computation_done = True
        self.send_data = False

    def init_approximate_pca(self):
        self.interation_counter = 0
        self.converged = False
        self.out = {'local_h': self.pca.H}
        self.computation_done = True
        self.send_data = False
        if self.federated_qr == QR.FEDERATED_QR:
            self.init_federated_qr()
        
    # def init_federated_qr(self):
    #     self.current_vector= 0
    #     self.orthonormalisation_done = False
    #     self.global_cornoms = []
    #     self.local_vector_conorms = []
    #     self.local_eigenvector_norm = -1
    #     self.all_global_eigenvector_norms = []


    def aggregate_eigenvector_norms(self, incoming):
        eigenvector_norm = 0
        for v in incoming:
            eigenvector_norm = eigenvector_norm + v['local_eigenvector_norm']

        eigenvector_norm = np.sqrt(eigenvector_norm)
        # increment the vector index after sending back the norms
        if self.current_vector == self.k:
            self.orthonormalisation_done = True
        self.out = {'global_eigenvector_norm': eigenvector_norm, 'orthonormalisation_done': self.orthonormalisation_done}
        self.computation_done = True
        self.send_data = True
        return True

    def aggregate_conorms(self, incoming):
        print('aggregating co norms')
        conorms = np.zeros(len(incoming[0]['local_conorms']))
        for n in incoming:
            conorms = np.sum([conorms, n['local_conorms']], axis=0)
        self.out = {'global_conorms': conorms}
        self.computation_done = True
        self.send_data = True

    def compute_local_eigenvector_norm(self):
        print('starting eigenvector norms')
        # not the euclidean norm, because the square root needs to be calculated
        # at the aggregator
        self.local_eigenvector_norm = np.dot(self.pca.G[:, self.current_vector],
                                  self.pca.G[:, self.current_vector])
        self.current_vector = self.current_vector + 1
        self.out = {'local_eigenvector_norm': self.local_eigenvector_norm}
        self.computation_done = True
        self.send_data = False
        return True

    def calculate_local_vector_conorms(self, incoming):
        vector_conorms = []
        # append the lastly calculated norm to the list of global norms
        self.all_global_eigenvector_norms.append(incoming['global_eigenvector_norm'])
        print('Computing local co norms')
        #print(vector_conorms)
        print(self.current_vector)
        #print(self.pca.G)
        for cvi in range(self.current_vector):
            vector_conorms.append(np.dot(self.pca.G[:, cvi], self.pca.G[:, self.current_vector]) / self.all_global_eigenvector_norms[cvi])
        print('done')
        self.local_vector_conorms = vector_conorms
        if self.current_vector == self.k:
            self.orthonormalisation_done = True
        self.out = {'local_conorms': self.local_vector_conorms}
        self.computation_done = True
        self.send_data = False
        return True


    def aggregate_local_subspaces(self, incoming):
        h_matrices = []
        for m in incoming:
            h_matrices.append(m['local_h'])

        h_matrices = np.concatenate(h_matrices, axis = 1)
        H, S, G , k = sh.svd_sub(h_matrices, self.k)
        if self.algorithm == 'approximate_pca':
            print('Converged')
            out = {'h_global': H, 'converged': True}
        else:
            # if approximate subspace is used as init method,
            # further iterations are required.
            out = {'h_global': H, 'converged': False}
        self.out = out
        self.send_data = True
        self.computation_done = True
        return True

