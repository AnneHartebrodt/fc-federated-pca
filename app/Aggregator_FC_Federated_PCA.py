from app.FC_Federated_PCA import FCFederatedPCA
import  numpy as np
from app.Steps import Step
import scipy as sc
import scipy.linalg as la
from app.PCA.shared_functions import eigenvector_convergence_checker

class AggregatorFCFederatedPCA(FCFederatedPCA):
    def __init__(self):
        self.dummy = None
        self.coordinator = True
        FCFederatedPCA.__init__(self)

    def finalize_parameter_setup(self):
        if self.scale_dim == 'rows':
            if self.center and self.scale_variance:
                self.step_queue = self.step_queue + [Step.WAIT_FOR_PARAMS, Step.READ_DATA,
                                                     Step.COMPUTE_LOCAL_SUMS, Step.COMPUTE_GLOBAL_MEANS,
                                                    Step.SCALE_DATA,
                                                 Step.COMPUTE_LOCAL_SUM_OF_SQUARES, Step.AGGREGATE_SUM_OF_SQUARES,
                                                 Step.SCALE_TO_UNIT_VARIANCE, Step.SAVE_SCALED_DATA, Step.INIT_POWER_ITERATION,
                                                     Step.AGGREGATE_H,
                                                     Step.COMPUTE_G_LOCAL]
            elif self.center:
                self.step_queue = self.step_queue + [Step.WAIT_FOR_PARAMS, Step.READ_DATA, Step.COMPUTE_LOCAL_SUMS,
                                                 Step.COMPUTE_GLOBAL_MEANS,
                                                 Step.SCALE_DATA, Step.SAVE_SCALED_DATA,Step.INIT_POWER_ITERATION,
                                                     Step.AGGREGATE_H,
                                                     Step.COMPUTE_G_LOCAL]
            elif self.scale_variance:
                self.step_queue = self.step_queue + [Step.WAIT_FOR_PARAMS, Step.READ_DATA,
                                                     Step.COMPUTE_LOCAL_SUM_OF_SQUARES, Step.AGGREGATE_SUM_OF_SQUARES,
                                                     Step.SCALE_TO_UNIT_VARIANCE, Step.SAVE_SCALED_DATA,
                                                     Step.INIT_POWER_ITERATION,
                                                     Step.AGGREGATE_H,
                                                     Step.COMPUTE_G_LOCAL
                                                     ]
            else:
                self.step_queue = self.step_queue + [Step.WAIT_FOR_PARAMS, Step.READ_DATA,
                                                     Step.INIT_POWER_ITERATION,
                                                     Step.AGGREGATE_H,
                                                     Step.COMPUTE_G_LOCAL]
        elif self.scale_dim == 'columns':
            self.step_queue = self.step_queue + [Step.WAIT_FOR_PARAMS, Step.READ_DATA, Step.SCALE_LOCALLY,
                                                 Step.SAVE_SCALED_DATA,
                                                 Step.INIT_POWER_ITERATION,
                                                 Step.AGGREGATE_H,
                                                 Step.COMPUTE_G_LOCAL]
        else:
            print('No scaling')

        # No user interaction required, set available to true
        # master still sends configuration to all clients.
        self.out = {'pcs': self.k,
                    'allow_rerun': self.allow_rerun,
                    'allow_transmission': self.allow_transmission,
                    'outlier_removal': self.outlier_removal}
        self.send_data = True
        self.computation_done = True
        print('[API] [COORDINATOR] /setup config done!')
        # if self.algorithm == 'power_iteration':
        #     self.step_queue = ['agree_on_row_names', 'normalize', 'init_power_iteration']
        # else:
        #     self.step_queue = ['normalize', 'pca']

        
    def compute_local_sums(self):
        try:
            sums = np.sum(self.tabdata.scaled, axis=0)
            outdata = {'sums': sums, 'sample_count': self.tabdata.col_count}
            self.out = outdata
            self.send_data = True
            self.computation_done = True
        except Exception as e:
            print('[API] computing local sums failed')

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

    def compute_global_means(self, data):
        means = np.zeros(data[0]['sums'].shape)
        total_count = 0
        for d in data:
            total_count += d['sample_count']
            means = np.sum([means, d['sums']], axis=0)
        means = means/total_count
        self.out = {'means': means}
        self.computation_done = True
        self.send_data = True
        return True

    def compute_global_sum_of_squares(self, incoming):
        vars = np.zeros(incoming[0]['sums'].shape)
        total_count = 0
        for d in incoming:
            vars = np.sum([vars, d['sums']], axis = 0)
            total_count = total_count + d['sample_count']
        vars = vars / (total_count - 1)
        vars = np.sqrt(vars)
        self.out = {'vars': vars}
        self.computation_done = True
        self.send_data = True
        return True

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

    def compute_g(self, incoming):
        self.pca.H = incoming['h_global']
        self.converged = incoming['converged']
        self.pca.G = np.dot(self.tabdata.scaled.T, self.pca.H)

        if self.federated_qr:
            # send local norms
            print('G computed')
            if self.federated_qr:
                # send local norms
                if self.converged:
                    self.step_queue = self.step_queue + [Step.COMPUTE_LOCAL_NORM, Step.AGGREGATE_NORM,
                                       Step.COMPUTE_LOCAL_CONORM, Step.AGGREGATE_CONORM, Step.ORTHOGONALISE_CURRENT] * (self.k - 1) + \
                                      [Step.COMPUTE_LOCAL_NORM, Step.AGGREGATE_NORM, Step.NORMALISE_G] + [Step.SAVE_SVD]

                    if self.show_result:
                        self.step_queue = self.step_queue + [Step.COMPUTE_PROJECTIONS, Step.SAVE_PROJECTIONS,
                                                             Step.SHOW_RESULT, Step.FINALIZE]
                    else:
                        self.step_queue = self.step_queue + [Step.FINALIZE]

                else:
                    self.step_queue = self.step_queue + \
                                      [Step.COMPUTE_LOCAL_NORM, Step.AGGREGATE_NORM,
                                       Step.COMPUTE_LOCAL_CONORM, Step.AGGREGATE_CONORM, Step.ORTHOGONALISE_CURRENT] * (self.k - 1) + \
                                      [Step.COMPUTE_LOCAL_NORM, Step.AGGREGATE_NORM, Step.NORMALISE_G] + \
                                      [Step.COMPUTE_H_LOCAL, Step.AGGREGATE_H, Step.COMPUTE_G_LOCAL]
                    print(self.step_queue)

                # next local step is to follow!
                self.computation_done = True
        else:
            if self.converged:
                self.step_queue = self.step_queue + [Step.ORTHONORMALISE_G, Step.SAVE_SVD, Step.FINALIZE]
            else:
                self.step_queue = self.step_queue + [Step.ORTHONORMALISE_G, Step.COMPUTE_H_LOCAL,
                                                     Step.AGGREGATE_H, Step.COMPUTE_G_LOCAL]
            self.send_data = False
            self.computation_done = True
            self.out = {'g_local': self.pca.G}
        print(self.step_queue)
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
        # transmit H matrix and convergence status to clients
        out = {'h_global': global_HI_matrix, 'converged': self.converged}
        self.out = out
        self.send_data = True
        self.computation_done = True
        return True

    def orthonormalise_g(self, incoming, client_order):

        print("Orthonormalisation step ...")

        # This is the order the clients were set in the setup call
        g_matrices = []
        samples_sizes = []
        last = 0
        client_indices = {}
        for c in client_order:
            gm = np.array(incoming[c]['g_local'])
            nrs = gm.shape[0]
            g_matrices.append(gm)
            samples_sizes.append(nrs)
            client_indices[c] = {'start': last, 'stop': last + nrs}
            last = last + nrs
        # stack the matrices. Now in the order of the clients from init
        global_GI_matrices = np.concatenate(g_matrices, axis=0)
        # Compute eigenvalues as the norm of the unnormalised vectors
        eigenvalues = []
        for col in range(global_GI_matrices.shape[1]):
            eigenvalues.append(la.norm(global_GI_matrices[:, col]))

        G, Q = la.qr(global_GI_matrices, mode='economic')

        g_matrices = {}
        # make sure to send the correct indices to the correct client
        # Currently everything is dumped naively to all clients
        for o in client_order:
            c = client_indices[o]
            g_matrices[o] = G[c['start']:c['stop'], :].tolist()

        self.out = {'g_matrices': g_matrices, 'eigenvalues': eigenvalues}
        print("Orthonormalisation done!")

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
        if self.federated_qr:
            self.orthonormalisation_done = False
            self.current_vector = 0
            self.global_cornoms = []
            self.local_vector_conorms = []
            self.local_eigenvector_norm = -1
            self.all_global_eigenvector_norms = []
        self.computation_done = True
        self.send_data = False

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

    def init_rerun(self):
        # remove outliers from data
        # copy svd object without samples
        # I guess technically data should be rescaled.
        # TODO rescale data.
        self.tabdata.scaled = np.delete(self.tabdata.scaled, self.outliers, axis=1)
        self.pca.G = np.delete(self.pca.G, self.outliers, axis=0)
        self.step_queue = self.step_queue + [Step.AGGREGATE_H, Step.COMPUTE_G_LOCAL]
        # reinit power iteration
        self.init_power_iteration()
        return True
