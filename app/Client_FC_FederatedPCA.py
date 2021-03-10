import app.TabData as TabData
import app.SVD as SVD
import numpy as np
from app.FC_Federated_PCA import FCFederatedPCA
import pandas as pd
import traceback
from app.Steps import Step
import copy

class ClientFCFederatedPCA(FCFederatedPCA):
    def __init__(self):
        self.dummy = None
        self.coordinator = False
        FCFederatedPCA.__init__(self)

    def finalize_parameter_setup(self):
        if self.center and self.scale_variance:
            self.step_queue = self.step_queue + [Step.WAIT_FOR_PARAMS, Step.READ_DATA, Step.COMPUTE_LOCAL_SUMS, Step.SCALE_DATA,
                                                 Step.COMPUTE_LOCAL_SUM_OF_SQUARES,
                                                 Step.SCALE_TO_UNIT_VARIANCE,  Step.SAVE_SCALED_DATA, Step.INIT_POWER_ITERATION,
                                                 Step.COMPUTE_G_LOCAL]
        elif self.center:
            self.step_queue = self.step_queue + [Step.WAIT_FOR_PARAMS, Step.READ_DATA, Step.COMPUTE_LOCAL_SUMS, Step.SCALE_DATA,
                                                 Step.SAVE_SCALED_DATA,
                                                 Step.INIT_POWER_ITERATION,
                                                 Step.COMPUTE_G_LOCAL]

        elif self.scale_variance:
            self.step_queue = self.step_queue + [Step.WAIT_FOR_PARAMS, Step.READ_DATA,
                                                 Step.COMPUTE_LOCAL_SUM_OF_SQUARES,
                                                 Step.SCALE_TO_UNIT_VARIANCE, Step.SAVE_SCALED_DATA, Step.INIT_POWER_ITERATION,
                                                 Step.COMPUTE_G_LOCAL]
        self.computation_done = True
        print('[API] [CLIENT] /setup config done!')
        # if self.algorithm == 'power_iteration':
        #     self.step_queue = ['init_algorithm', 'agree_on_row_names', 'init_power_iteration']
        # else:
        #     self.step_queue = ['init_algorithm', 'pca']

    def compute_local_sums(self):
        try:
            sums = np.sum(self.tabdata.data, axis=0)
            outdata = {'sums': sums, 'sample_count': self.tabdata.row_count}
            self.out = outdata
            self.send_data = True
            self.computation_done = True
        except Exception as e:
            print('[API] computing local sums failed')
            traceback.print_exc()

        return True

    def compute_local_sum_of_squares(self):
        vars = np.sum(np.square(self.tabdata.data), axis=0)
        outdata = {'sums': vars, 'sample_count': self.tabdata.row_count}
        self.out = outdata
        self.send_data = True
        self.computation_done = True
        return True

    def compute_h(self, incoming, client_id):
            # Compute dot product of data and G_i
        print('Aggregating')
        self.pca.G = incoming['g_matrices'][client_id]
        self.pca.S = incoming['eigenvalues']
        self.pca.H = np.dot(self.tabdata.scaled, self.pca.G)
        print('Aggregation done')
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

    def compute_g(self, incoming):
        self.pca.H = incoming['h_global']
        self.converged = incoming['converged']
        self.pca.G = np.dot(self.tabdata.scaled.T, self.pca.H)

        print('G computed')
        if self.federated_qr:
            # send local norms
            if self.converged:
                self.step_queue = self.step_queue + [Step.COMPUTE_LOCAL_NORM, Step.COMPUTE_LOCAL_CONORM, Step.ORTHOGONALISE_CURRENT]*(self.k-1)+\
                                  [Step.COMPUTE_LOCAL_NORM, Step.NORMALISE_G] + [Step.SAVE_SVD]

                if self.show_result:
                    self.step_queue = self.step_queue + [Step.COMPUTE_PROJECTIONS, Step.SAVE_PROJECTIONS,
                                                         Step.SHOW_RESULT, Step.FINALIZE]
                else:
                    self.step_queue = self.step_queue + [Step.FINALIZE]

            else:
                self.step_queue = self.step_queue + [Step.COMPUTE_LOCAL_NORM, Step.COMPUTE_LOCAL_CONORM, Step.ORTHOGONALISE_CURRENT]*(self.k-1)+\
                                  [Step.COMPUTE_LOCAL_NORM, Step.NORMALISE_G] + [Step.COMPUTE_H_LOCAL, Step.COMPUTE_G_LOCAL]
                print(self.step_queue)
            # next local step is to follow!
            self.computation_done = True
        else:
            if self.converged:
                self.step_queue = self.step_queue + [Step.WAIT_FOR_G, Step.SAVE_SVD, Step.FINALIZE]
            else:
                self.step_queue = self.step_queue + [Step.COMPUTE_H_LOCAL, Step.COMPUTE_G_LOCAL]
            self.send_data = True
            self.computation_done = True
            self.out = {'g_local': self.pca.G}
        return True


    def init_power_iteration(self):
        self.iteration_counter = 0
        self.converged = False
        print(self.pca.G.shape)
        print(self.tabdata.scaled.shape)
        self.pca.H = np.dot(self.tabdata.scaled, self.pca.G)
        self.out = {'local_h': self.pca.H}
        if self.federated_qr:
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



#def scale_datasets(data_list):
    # sums = []
    # sample_count = 0
    #
    # # mean
    # sums = [np.sum(d, axis = 0) for d in data_list]
    # sums = np.sum(sums, axis=0)
    # sample_count = [d.shape[0] for d in data_list]
    # total_count = sum(sample_count)
    # means = [s/total_count for s in sums]
    # for i in range(len(data_list)):
    #     data_list[i] = data_list[i] - means
    #
    # #variance
    #
    # vars = [np.sum(np.square(d), axis=0) for d in data_list]
    # vars = np.sum(vars, axis = 0)
    # vars = vars/(total_count-1)
    # # variance  = 0
    # delete = np.where(vars==0)
    # vars = np.delete(vars, delete)
    # for i in range(len(data_list)):
    #     data_list[i] = np.delete(data_list[i], delete, axis=1)
    #
    # for i in range(len(data_list)):
    #     data_list[i] = data_list[i]/np.sqrt(vars)
    # return data_list