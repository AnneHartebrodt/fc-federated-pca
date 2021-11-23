from app.FC_Federated_PCA import FCFederatedPCA
import  numpy as np
from app.Steps import Step
import scipy as sc
import scipy.linalg as la
from app.PCA.shared_functions import eigenvector_convergence_checker
from app.algo_params import QR, PCA_TYPE
import app.PCA.shared_functions as sh
from app.COParams import COParams

class AggregatorFCFederatedPCA(FCFederatedPCA):
    def __init__(self):
        self.dummy = None
        self.coordinator = True
        FCFederatedPCA.__init__(self)

    def finalize_parameter_setup(self):
        self.step_queue = self.step_queue + [Step.WAIT_FOR_PARAMS,Step.READ_DATA]
        if self.algorithm == PCA_TYPE.APPROXIMATE:
            self.step_queue = self.step_queue + [Step.APPROXIMATE_LOCAL_PCA]
            if self.use_smpc:
                self.step_queue = self.step_queue + [Step.AGGREGATE_COVARIANCE]
            else:
                self.step_queue = self.step_queue + [Step.AGGREGATE_SUBSPACES]
            self.queue_shutdown()
        elif self.algorithm == PCA_TYPE.COVARIANCE:
            self.step_queue = self.step_queue + [Step.COMPUTE_COVARIANCE,
                                                 Step.AGGREGATE_COVARIANCE]
            self.queue_shutdown()
        elif self.algorithm == PCA_TYPE.QR_PCA:
            self.step_queue = self.step_queue + [Step.COMPUTE_QR,
                                                 Step.AGGREGATE_QR]
            self.queue_shutdown()
        elif self.algorithm == PCA_TYPE.POWER_ITERATION:
            if self.init_method == PCA_TYPE.APPROXIMATE:
                self.step_queue = self.step_queue + [Step.APPROXIMATE_LOCAL_PCA,
                                                     Step.AGGREGATE_SUBSPACES]
            else:
                self.step_queue = self.step_queue + [Step.INIT_POWER_ITERATION, Step.AGGREGATE_H]

            if self.federated_qr == QR.NO_QR:
                print('pass')
                #self.step_queue = self.step_queue + [Step.UPDATE_H, Step.AGGREGATE_H]
            else:
                self.step_queue = self.step_queue + [Step.COMPUTE_G_LOCAL]
        else:
            self.step_queue = [Step.FINALIZE]

        print('[API] [COORDINATOR] /setup config done!')
        # No user interaction required, set available to true
        # master still sends configuration to all clients.
        self.out = {COParams.PCS.n: self.k}
        print(self.step_queue)
        self.send_data = True
        self.computation_done = True
        print('[API] [COORDINATOR] /setup config done!')


    def compute_h_local_g(self):
        # this is the case for federated PCA and the first iteration
        # of centralised PCA
        super(AggregatorFCFederatedPCA, self).compute_h_local_g()
        self.computation_done = True
        # send data if smpc is used
        self.send_data = self.use_smpc
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
        self.pca.H = incoming[COParams.H_GLOBAL.n]
        self.converged = incoming[COParams.CONVERGED.n]
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
        self.update_progess()
        # First, update the local G estimate
        self.pca.H = incoming[COParams.H_GLOBAL.n]
        self.pca.G = np.dot(self.tabdata.scaled.T, self.pca.H)
        self.pca.S = np.linalg.norm(self.pca.G, axis=1)

        # Then check for convergence.
        self.converged = incoming[COParams.CONVERGED.n]
        self.pca.previous_h = self.pca.H
        # if self.converged:
        #     self.pca.H = incoming[COParams.H_GLOBAL.n]
        #     self.queue_shutdown()
        # else:
        #     # changed step queing
        #     self.pca.H = np.dot(self.tabdata.scaled, self.pca.G)
        # # If convergence not reached, update H and go on
        #     self.out = {COParams.H_LOCAL.n: self.pca.H}


        self.pca.H = np.dot(self.tabdata.scaled, self.pca.G)
        # If convergence not reached, update H and go on
        self.out = {COParams.H_LOCAL.n: self.pca.H}
        self.computation_done = True
        # send data if smpc is used
        self.send_data = self.use_smpc
        return True

    def aggregate_h(self, incoming):
        '''
        This step adds up the H matrices (nr_SNPs x target dimension) matrices to
        achieve a global H matrix
        :param parameters_from_clients: The local H matrices
        :return: Global H matrix to be sent to the client
        '''

        print("Adding up H matrices from clients ...")
        if self.use_smpc:
            global_HI_matrix = np.array(incoming[0][COParams.H_LOCAL.n])
        else:
            global_HI_matrix = np.zeros(self.pca.H.shape)
            for m in incoming:
                global_HI_matrix += m[COParams.H_LOCAL.n]
            print('H matrices added up')
        global_HI_matrix, R = la.qr(global_HI_matrix, mode='economic')
        self.iteration_counter = self.iteration_counter + 1
        print(self.iteration_counter)
        # The previous H matrix is stored in the global variable
        print('Orthonormalised')
        converged, deltas = eigenvector_convergence_checker(global_HI_matrix, self.pca.previous_h, tolerance=self.epsilon)
        if self.iteration_counter == self.max_iterations or converged:
            self.step_queue = self.step_queue + [Step.COMPUTE_G_LOCAL]
            self.queue_qr()
            self.queue_shutdown()
            self.converged = True
            print('CONVERGED')
        else:
            if self.federated_qr == QR.NO_QR:
                self.step_queue = self.step_queue + [Step.UPDATE_H, Step.AGGREGATE_H]
        out = {COParams.H_GLOBAL.n: global_HI_matrix, COParams.CONVERGED.n: self.converged}
        self.out = out
        self.send_data = True
        self.computation_done = True
        return True

    def init_power_iteration(self):
        super(AggregatorFCFederatedPCA, self).init_power_iteration()
        self.iteration_counter = self.iteration_counter + 1

        self.computation_done = True
        # send data if smpc is used
        self.send_data = self.use_smpc

    def init_approximate_pca(self):
        super(AggregatorFCFederatedPCA, self).init_approximate_pca()
        self.iteration_counter = self.iteration_counter + 1

        self.computation_done = True
        # send data if smpc is used
        self.send_data = self.use_smpc

    def aggregate_eigenvector_norms(self, incoming):
        if self.use_smpc:
            eigenvector_norm = incoming[0][COParams.LOCAL_EIGENVECTOR_NORM.n]
        else:
            eigenvector_norm = 0
            for v in incoming:
                eigenvector_norm = eigenvector_norm + v[COParams.LOCAL_EIGENVECTOR_NORM.n]

        eigenvector_norm = np.sqrt(eigenvector_norm)
        # increment the vector index after sending back the norms
        if self.current_vector == self.k:
            self.orthonormalisation_done = True
        self.out = {COParams.GLOBAL_EIGENVECTOR_NORM.n: eigenvector_norm, COParams.ORTHONORMALISATION_DONE.n: self.orthonormalisation_done}
        self.computation_done = True
        self.send_data = True
        return True

    def aggregate_conorms(self, incoming):
        print('aggregating co norms')
        print(incoming)
        if self.use_smpc:
            conorms = np.array(incoming[0][COParams.LOCAL_CONORMS.n])
        else:
            conorms = np.zeros(len(incoming[0][COParams.LOCAL_CONORMS.n]))
            for n in incoming:
                conorms = np.sum([conorms, n[COParams.LOCAL_CONORMS.n]], axis=0)
        self.out = {COParams.GLOBAL_CONORMS.n: conorms}
        self.computation_done = True
        self.send_data = True

    def compute_local_eigenvector_norm(self):
        super(AggregatorFCFederatedPCA, self).compute_local_eigenvector_norm()        
        self.computation_done = True
        # send data if smpc is used
        self.send_data = self.use_smpc
        return True

    def calculate_local_vector_conorms(self, incoming):
        super(AggregatorFCFederatedPCA, self).calculate_local_vector_conorms(incoming)
        self.computation_done = True
        # send data if smpc is used
        self.send_data = self.use_smpc
        return True

    def aggregate_local_subspaces(self, incoming):
        h_matrices = []
        if self.algorithm == PCA_TYPE.COVARIANCE or (self.algorithm==PCA_TYPE.APPROXIMATE and self.use_smpc):
            if self.use_smpc:
                #allready aggregated only 1 element in list
                h_matrices = np.array(incoming[0][COParams.COVARIANCE_MATRIX.n])
            else:
                for m in incoming:
                    h_matrices.append(m[COParams.COVARIANCE_MATRIX.n])
                # element wise addition
                h_matrices = np.nansum(h_matrices, axis=0)
        else: #self.algorithm == PCA_TYPE.APPROXIMATE:
            for m in incoming:
                h_matrices.append(m[COParams.H_LOCAL.n])
            h_matrices = np.concatenate(h_matrices, axis = 1)
        H, S, G , k = sh.svd_sub(h_matrices, self.k)
        if self.algorithm == PCA_TYPE.APPROXIMATE or self.algorithm == PCA_TYPE.COVARIANCE:
            print('Converged')
            out = {COParams.H_GLOBAL.n: H, COParams.CONVERGED.n: True}
        else:
            # if approximate subspace is used as init method,
            # further iterations are required.
            out = {COParams.H_GLOBAL.n: H, COParams.CONVERGED.n: False}
        self.iteration_counter = self.iteration_counter + 1
        self.out = out
        self.send_data = True
        self.computation_done = True
        return True

    def compute_covariance(self):
        super(AggregatorFCFederatedPCA, self).compute_covariance()
        self.iteration_counter = self.iteration_counter + 1
        self.computation_done = True
        # send data if smpc is used
        self.send_data = self.use_smpc
        return True

    def compute_qr(self):
        super(AggregatorFCFederatedPCA, self).compute_qr()
        self.iteration_counter = self.iteration_counter + 1
        self.computation_done = True
        # Not compatible with SMPC
        self.send_data = False
        return True

    def aggregate_qr(self, incoming):
        print('Aggregating R matrices')
        r_matrices = []
        for m in incoming:
            r_matrices.append(m[COParams.R.n])

        r_matrices = np.concatenate(r_matrices, axis=0)
        q,r  = la.qr(r_matrices, mode='economic')
        u, s,v, nd  = sh.svd_sub(r, ndims=self.k)
        self.out = {COParams.H_GLOBAL.n: v}
        self.computation_done = True
        self.send_data = True
        print('Aggregating R matrices ... DONE!')


