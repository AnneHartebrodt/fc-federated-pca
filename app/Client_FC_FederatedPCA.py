import app.TabData as TabData
import app.SVD as SVD
import numpy as np
from app.FC_Federated_PCA import FCFederatedPCA
import pandas as pd
import traceback
from app.Steps import Step
import copy
from app.QR_params import QR

class ClientFCFederatedPCA(FCFederatedPCA):
    def __init__(self):
        self.dummy = None
        self.coordinator = False
        FCFederatedPCA.__init__(self)

    def finalize_parameter_setup(self):
        self.step_queue = self.step_queue + [Step.WAIT_FOR_PARAMS,
                           Step.READ_DATA]
        if self.algorithm == 'approximate_pca':
            self.step_queue = self.step_queue + [Step.APPROXIMATE_LOCAL_PCA,
                                                 Step.UPDATE_H]

        if self.algorithm == 'power_iteration':
            if self.init_method == 'approximate_pca':
                self.step_queue = self.step_queue + [Step.APPROXIMATE_LOCAL_PCA]
            else:
                self.step_queue = self.step_queue + [Step.INIT_POWER_ITERATION]

            if self.federated_qr == QR.NO_QR:
                self.step_queue = self.step_queue + [Step.UPDATE_H]
            else:
                self.step_queue = self.step_queue + [Step.COMPUTE_G_LOCAL]

        self.computation_done = True
        print(self.step_queue)
        print('[API] [CLIENT] /setup config done!')

    def compute_local_sums(self):
        try:
            sums = np.sum(self.tabdata.scaled, axis=0)
            outdata = {'sums': sums, 'sample_count': self.tabdata.col_count}
            self.out = outdata
            self.send_data = True
            self.computation_done = True
        except Exception as e:
            print('[API] computing local sums failed')
            traceback.print_exc()

        return True

    def compute_local_sum_of_squares(self):
        try:
            vars = np.sum(np.square(self.tabdata.scaled), axis=0)
            outdata = {'sums': vars, 'sample_count': self.tabdata.col_count}
            self.out = outdata
            self.send_data = True
            self.computation_done = True
        except:
            print('Scaling locally failed')
        return True

    def compute_h(self, incoming, client_id):
            # Compute dot product of data and G_i
        print('Computing H')
        self.pca.G = incoming['g_matrices'][client_id]
        self.pca.S = incoming['eigenvalues']
        self.pca.H = np.dot(self.tabdata.scaled, self.pca.G)
        #print(self.pca.H)
        print('...done')
        self.out = {'local_h': self.pca.H}
        self.computation_done = True
        self.send_data = True
        return True

    def compute_h_local_g(self):
        # this is the case for federated PCA and the first iteration
        # of centralised PCA
        self.pca.H = np.dot(self.tabdata.scaled, self.pca.G)
        self.out = {'local_h': self.pca.H}
        self.computation_done = True
        self.send_data = True
        return True



    def update_h(self, incoming):

        # First, update the local G estimate
        self.pca.G = np.dot(self.tabdata.scaled.T, incoming['h_global'])
        self.pca.S = np.linalg.norm(self.pca.G, axis=1)

        # Then check for convergence.
        self.converged = incoming['converged']
        if self.converged:
            self.queue_shutdown()
        else:
            self.step_queue = self.step_queue + [Step.UPDATE_H]

        # If convergence not reached, update H and go on
        self.pca.H = np.dot(self.tabdata.scaled, self.pca.G)
        self.out = {'local_h': self.pca.H}
        self.computation_done = True
        self.send_data = True
        return True

    def queue_qr(self):
            self.step_queue = self.step_queue + [Step.COMPUTE_LOCAL_NORM,
                                                 Step.COMPUTE_LOCAL_CONORM,
                                                 Step.ORTHOGONALISE_CURRENT] * (self.k - 1) +\
                                                [Step.COMPUTE_LOCAL_NORM,
                                                 Step.NORMALISE_G]

    def compute_g(self, incoming):
        self.pca.H = incoming['h_global']
        self.converged = incoming['converged']
        self.pca.G = np.dot(self.tabdata.scaled.T, self.pca.H)

        if self.federated_qr == QR.FEDERATED_QR:
            self.queue_qr()
        if self.converged:
            self.queue_shutdown()
        else:
            self.step_queue = self.step_queue + [Step.COMPUTE_H_LOCAL, Step.COMPUTE_G_LOCAL]
        print(self.step_queue)
        self.computation_done = True
        return True


    def init_power_iteration(self):
        self.iteration_counter = 0
        self.converged = False
        print(self.pca.G.shape)
        print(self.tabdata.scaled.shape)
        self.pca.H = np.dot(self.tabdata.scaled, self.pca.G)
        self.out = {'local_h': self.pca.H}
        if self.federated_qr == QR.FEDERATED_QR:
            self.init_federated_qr()
        self.computation_done = True
        self.send_data = True

    def init_approximate_pca(self):
        self.interation_counter = 0
        self.converged = False
        self.out = {'local_h': self.pca.H}
        if self.federated_qr == QR.FEDERATED_QR:
            self.init_federated_qr()
        self.computation_done = True
        self.send_data = True


    def init_federated_qr(self):
        self.current_vector= 0
        self.orthonormalisation_done = False
        self.global_cornoms = []
        self.local_vector_conorms = []
        self.local_eigenvector_norm = -1
        self.all_global_eigenvector_norms = []


    def wait_for_g(self, incoming, client_id):
        self.pca.G = incoming['g_matrices'][client_id]
        self.pca.S = incoming['eigenvalues']
        self.computation_done = True
        self.send_data = False
        return True

    def compute_local_eigenvector_norm(self):
        print('starting eigenvector norms')
        # not the euclidean norm, because the square root needs to be calculated
        # at the aggregator
        print(self.current_vector)
        self.local_eigenvector_norm = np.dot(self.pca.G[:, self.current_vector], self.pca.G[:, self.current_vector])
        self.current_vector = self.current_vector + 1
        self.out = {'local_eigenvector_norm': self.local_eigenvector_norm}
        self.computation_done = True
        self.send_data = True
        return True

    def calculate_local_vector_conorms(self, incoming):
        vector_conorms = []
        # append the lastly calculated norm to the list of global norms
        self.all_global_eigenvector_norms.append(incoming['global_eigenvector_norm'])
        print('Computing local co norms')
        for cvi in range(self.current_vector):
            vector_conorms.append(
                np.dot(self.pca.G[:, cvi], self.pca.G[:, self.current_vector]) / self.all_global_eigenvector_norms[cvi])
        self.local_vector_conorms = vector_conorms
        if self.current_vector == self.k:
            self.orthonormalisation_done = True
        self.out = {'local_conorms': self.local_vector_conorms}
        self.computation_done = True
        self.send_data = True
        return True
