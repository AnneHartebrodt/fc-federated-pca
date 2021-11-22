import yaml
import os
import re
import os.path as op
from app.params import INPUT_DIR, OUTPUT_DIR
from app.TabData import TabData
import pandas as pd
import traceback
from app.Steps import Step
import numpy as np
import copy
from app.algo_params import QR
from shutil import copyfile
from shutil import copyfile
from app.SVD import SVD
from app.params import INPUT_DIR, OUTPUT_DIR
import pathlib as pl
import scipy.linalg as la
from app.COParams import COParams
import time

class FCFederatedPCA:
    def __init__(self):
        self.step = 0
        self.tabdata = None
        self.pca = None
        self.config_available = False
        self.out = None
        self.send_data = False
        self.computation_done = False
        self.coordinator = False
        self.step_queue = [] # this is the initial step queue
        self.state = 'waiting_for_start' # this is the inital state
        self.iteration_counter = 0
        self.converged = False
        self.outliers = []
        self.approximate_pca = True
        self.data_incoming = {}
        self.progress = 0.0
        self.silent_step=False
        self.use_smpc = False
        self.start_time = time.monotonic()

    def next_state(self):
        self.state = self.step_queue.pop(0)
        return self.state

    def peek_next_state(self):
        try:
            return self.step_queue[0]
        except:
            print('No more states')

    def get_state(self):
        return self.state

    def copy_configuration(self, config, directory, train=''):
        print('Copy configuration')
        self.config_available = config.config_available
        self.batch = config.batch
        self.directories = config.directories
        self.input_file = op.join(INPUT_DIR, directory, train, config.input_file)
        self.left_eigenvector_file = op.join(OUTPUT_DIR, directory, train,  config.left_eigenvector_file)
        self.right_eigenvector_file = op.join(OUTPUT_DIR, directory, train, config.right_eigenvector_file)
        self.eigenvalue_file = op.join(OUTPUT_DIR, directory, train, config.eigenvalue_file)
        self.projection_file = op.join(OUTPUT_DIR, directory, train, config.projection_file)
        self.log_file = op.join(OUTPUT_DIR, directory, train, 'run_log.txt')
        self.k = config.k
        self.algorithm = config.algorithm
        self.federated_qr = config.federated_qr
        self.max_iterations = config.max_iterations
        self.use_smpc = config.use_smpc
        self.epsilon = config.epsilon
        self.init_method = config.init_method

        self.sep = config.sep
        self.has_rownames = config.has_rownames
        self.has_colnames = config.has_colnames
        self.allow_transmission = config.allow_transmission
        self.encryption = config.encryption

        print('[Client] Configuation copied')

    def update_progess(self):
        ## allow 60 percent of the progress bar for the iterations
        self.progress = 0.2 + (self.iteration_counter/self.max_iterations)*0.6

    def read_input_files(self):
        try:
            self.progress = 0.1
            self.tabdata = TabData.from_file(self.input_file, header=self.has_colnames,
                                             index=self.has_rownames, sep=self.sep)
            self.computation_done = True
        except Exception as e:
            print('[API] reading data failed')
            print(traceback.print_exc())


    def init_random(self):
        print('init random')
        self.progress = 0.2
        self.pca = SVD.init_random(self.tabdata, k=self.k)
        self.k = self.pca.k
        return True

    def init_approximate(self):
        self.progress = 0.2
        self.pca = SVD.init_local_subspace(self.tabdata, k=self.k)
        self.k = self.pca.k
        return True

    def compute_covariance(self):
        self.init_random()
        self.progress = 0.2
        self.covariance = np.dot(self.tabdata.scaled, self.tabdata.scaled.T)
        self.k = self.pca.k
        self.out = {COParams.COVARIANCE_MATRIX.n: self.covariance}
        return True


    def set_parameters(self, incoming):
        try:
            print('[API] setting parameters')
            self.k = incoming[COParams.PCS.n]
            self.computation_done = True
        except Exception as e:
            print('[API] setting parameters failed')
            traceback.print_exc()
        return True

    def save_scaled_data(self):
        saveme = pd.DataFrame(self.tabdata.scaled)
        #saveme.columns = self.tabdata.columns
        #saveme.rows = self.tabdata.rows
        saveme.to_csv(self.scaled_data_file, header=False, index=False, sep='\t')
        self.computation_done = True
        self.send_data = False
        return True

    def update_and_save_pca(self, incoming):
        self.save_logs()
        # update PCA and save
        self.pca.G = np.dot(self.tabdata.scaled.T, incoming[COParams.H_GLOBAL.n])
        self.pca.H = incoming[COParams.H_GLOBAL.n]
        self.pca.S = np.linalg.norm(self.pca.G, axis=1)
        self.pca.to_csv(self.left_eigenvector_file, self.right_eigenvector_file, self.eigenvalue_file)
        self.computation_done = True
        self.send_data = False

    def save_pca(self):
        # update PCA and save
        self.save_logs()
        self.pca.to_csv(self.left_eigenvector_file, self.right_eigenvector_file, self.eigenvalue_file)
        self.computation_done = True
        self.send_data = False

    def save_logs(self):
        with open(self.log_file, 'w') as handle:
            handle.write('iterations:\t'+str(self.iteration_counter)+'\n')
            handle.write('runtime:\t' + str(time.monotonic()-self.start_time)+'\n')

    def orthogonalise_current(self, incoming):
        print('starting orthogonalise_current')
        self.global_conorms = incoming[COParams.GLOBAL_CONORMS.n]
        # update every cell individually
        for gp in range(len(self.global_conorms)):
            for row in range(self.pca.G.shape[0]):
                self.pca.G[row, self.current_vector] = self.pca.G[row, self.current_vector] - \
                                                      self.pca.G[row, gp] * self.global_conorms[gp]
        print('ending orthogonalise_current')
        self.computation_done = True
        self.send_data = False

    def normalise_orthogonalised_matrix(self, incoming):

        print('Normalising')
        # get the last eigenvector norm
        self.all_global_eigenvector_norms.append(incoming[COParams.GLOBAL_EIGENVECTOR_NORM.n])

        # divide all elements through the respective vector norm.
        for col in range(self.pca.G.shape[1]):
            for row in range(self.pca.G.shape[0]):
                self.pca.G[row, col] = self.pca.G[row, col] / self.all_global_eigenvector_norms[col]

        # reset eigenvector norms
        # Store current eigenvalue guess
        self.pca.S = copy.deepcopy(self.all_global_eigenvector_norms)

        self.current_vector = 0
        self.all_global_eigenvector_norms = []
        self.orthonormalisation_done = False
        self.computation_done = True
        self.send_data = False
        print('End normalising')

    def compute_projections(self):
        try:
            self.pca.projections = np.dot(self.tabdata.scaled.T, self.pca.H)
            self.computation_done = True
            self.send_data = False
        except:
            print('Failed computing projections')

    def save_projections(self):
        self.pca.save_projections(self.projection_file, sep='\t')
        self.computation_done = True
        self.send_data = False

    def save_outliers(self):
        if len(self.outliers) > 0:
            ol = self.tabdata.rows[self.outliers]
            pd.DataFrame(ol).to_csv(op.join(OUTPUT_DIR, 'outliers.tsv'), header=False, sep='\t')
        self.computation_done = True
        self.send_data = False

    def queue_shutdown(self):
        self.progress = 0.9
        self.step_queue = self.step_queue + [Step.SAVE_SVD, Step.COMPUTE_PROJECTIONS, Step.SAVE_PROJECTIONS,
                                             Step.FINALIZE]

    def init_federated_qr(self):
        self.orthonormalisation_done = False
        self.current_vector = 0
        self.global_cornoms = []
        self.local_vector_conorms = []
        self.local_eigenvector_norm = -1
        self.all_global_eigenvector_norms = []

    def init_power_iteration(self):
        self.iteration_counter = 0
        self.converged = False
        self.pca.H = np.dot(self.tabdata.scaled, self.pca.G)
        self.out = {COParams.H_LOCAL.n: self.pca.H}
        if self.federated_qr == QR.FEDERATED_QR:
            self.init_federated_qr()

    def init_approximate_pca(self):
        self.iteration_counter = 0
        self.converged = False
        if self.use_smpc:
            proxy_covariance = np.dot(self.pca.H, self.pca.H.T)
            self.out = {COParams.COVARIANCE_MATRIX.n: proxy_covariance}
        else:
            self.out = {COParams.H_LOCAL.n: self.pca.H}
        if self.federated_qr == QR.FEDERATED_QR:
            self.init_federated_qr()

    def compute_h_local_g(self):
        self.update_progess()
        self.pca.H = np.dot(self.tabdata.scaled, self.pca.G)
        self.out = {COParams.H_LOCAL.n: self.pca.H}
        return True

    def calculate_local_vector_conorms(self, incoming):
        vector_conorms = []
        # append the lastly calculated norm to the list of global norms
        self.all_global_eigenvector_norms.append(incoming[COParams.GLOBAL_EIGENVECTOR_NORM.n])
        for cvi in range(self.current_vector):
            vector_conorms.append(np.dot(self.pca.G[:, cvi], self.pca.G[:, self.current_vector]) / self.all_global_eigenvector_norms[cvi])
        self.local_vector_conorms = vector_conorms
        if self.current_vector == self.k:
            self.orthonormalisation_done = True
        self.out = {COParams.LOCAL_CONORMS.n: self.local_vector_conorms}
        return True

    def compute_local_eigenvector_norm(self):
        print('starting eigenvector norms')
        # not the euclidean norm, because the square root needs to be calculated
        # at the aggregator
        self.local_eigenvector_norm = np.dot(self.pca.G[:, self.current_vector],
                                  self.pca.G[:, self.current_vector])
        self.current_vector = self.current_vector + 1
        self.out = {COParams.LOCAL_EIGENVECTOR_NORM.n: self.local_eigenvector_norm}
        return True

    def compute_qr(self):
        self.init_random()
        q, self.r = la.qr(self.tabdata.scaled.T, mode='economic')
        self.out = {COParams.R.n: self.r}
        return True