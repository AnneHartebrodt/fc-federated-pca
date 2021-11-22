import app.TabData as TabData
import app.SVD as SVD
import numpy as np
from app.FC_Federated_PCA import FCFederatedPCA
import pandas as pd
import traceback
from app.Steps import Step
import copy
from app.algo_params import QR, PCA_TYPE
from app.COParams import COParams

class ClientFCFederatedPCA(FCFederatedPCA):
    def __init__(self):
        self.dummy = None
        self.coordinator = False
        FCFederatedPCA.__init__(self)

    def finalize_parameter_setup(self):
        self.step_queue = self.step_queue + [Step.WAIT_FOR_PARAMS,
                           Step.READ_DATA]
        if self.algorithm == PCA_TYPE.APPROXIMATE:
            self.step_queue = self.step_queue + [Step.APPROXIMATE_LOCAL_PCA]
            self.queue_shutdown()

        elif self.algorithm == PCA_TYPE.COVARIANCE:
            self.step_queue = self.step_queue + [Step.COMPUTE_COVARIANCE]
            self.queue_shutdown()
        elif self.algorithm == PCA_TYPE.QR_PCA:
            self.step_queue = self.step_queue + [Step.COMPUTE_QR]
            self.queue_shutdown()

        if self.algorithm == PCA_TYPE.POWER_ITERATION:
            if self.init_method == PCA_TYPE.APPROXIMATE:
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


    def compute_h_local_g(self):
        # this is the case for federated PCA and the first iteration
        # of centralised PCA
        super(ClientFCFederatedPCA, self).compute_h_local_g()
        self.computation_done = True
        self.send_data = True
        return True

    def update_h(self, incoming):
        self.update_progess()
        self.iteration_counter = self.iteration_counter + 1
        # First, update the local G estimate
        self.pca.G = np.dot(self.tabdata.scaled.T, incoming[COParams.H_GLOBAL.n])
        self.pca.S = np.linalg.norm(self.pca.G, axis=1)

        # Then check for convergence.
        self.converged = incoming[COParams.CONVERGED.n]
        if self.converged:
            self.pca.H = incoming[COParams.H_GLOBAL.n]
            self.queue_shutdown()
            self.send_data = False
        else:
            self.step_queue = self.step_queue + [Step.UPDATE_H]
            # If convergence not reached, update H and go on
            self.pca.H = np.dot(self.tabdata.scaled, self.pca.G)
            self.out = {COParams.H_LOCAL.n: self.pca.H}
            self.send_data = True
        self.computation_done = True

        return True

    def queue_qr(self):
            self.step_queue = self.step_queue + [Step.COMPUTE_LOCAL_NORM,
                                                 Step.COMPUTE_LOCAL_CONORM,
                                                 Step.ORTHOGONALISE_CURRENT] * (self.k - 1) +\
                                                [Step.COMPUTE_LOCAL_NORM,
                                                 Step.NORMALISE_G]

    def compute_g(self, incoming):
        self.pca.H = incoming[COParams.H_GLOBAL.n]
        self.converged = incoming[COParams.CONVERGED.n]
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
        super(ClientFCFederatedPCA, self).init_power_iteration()
        self.iteration_counter = self.iteration_counter + 1
        self.computation_done = True
        self.send_data = True

    def init_approximate_pca(self):
        super(ClientFCFederatedPCA, self).init_approximate_pca()
        self.iteration_counter = self.iteration_counter + 1
        self.computation_done = True
        self.send_data = True

    def compute_local_eigenvector_norm(self):
        super(ClientFCFederatedPCA, self).compute_local_eigenvector_norm()
        self.computation_done = True
        self.send_data = True
        return True

    def calculate_local_vector_conorms(self, incoming):
        super(ClientFCFederatedPCA, self).calculate_local_vector_conorms(incoming)
        self.computation_done = True
        self.send_data = True
        return True

    def compute_covariance(self):
        super(ClientFCFederatedPCA, self).compute_covariance()
        self.iteration_counter = self.iteration_counter + 1
        self.computation_done = True
        self.send_data = True
        return True

    def compute_qr(self):
        super(ClientFCFederatedPCA,self).compute_qr()
        self.iteration_counter = self.iteration_counter + 1
        self.computation_done = True
        self.send_data = True
        return True