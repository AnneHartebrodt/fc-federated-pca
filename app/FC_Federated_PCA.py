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
from app.QR_params import QR
from shutil import copyfile
from shutil import copyfile
from app.SVD import SVD
from app.params import INPUT_DIR, OUTPUT_DIR
import pathlib as pl

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
        self.config_available = config.config_available
        self.batch = config.batch
        self.directories = config.directories
        self.input_file = op.join(INPUT_DIR, directory, train, config.input_file)
        self.left_eigenvector_file = op.join(OUTPUT_DIR, directory, train,  config.left_eigenvector_file)
        self.right_eigenvector_file = op.join(OUTPUT_DIR, directory, train, config.right_eigenvector_file)
        self.eigenvalue_file = op.join(OUTPUT_DIR, directory, train, config.eigenvalue_file)
        self.projection_file = op.join(OUTPUT_DIR, directory, train, config.projection_file)
        self.k = config.k
        self.algorithm = config.algorithm
        self.federated_qr = config.federated_qr
        self.max_iterations = config.max_iterations
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


    def set_parameters(self, incoming):
        try:
            print('[API] setting parameters')
            self.k = incoming['pcs']
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
        # update PCA and save
        self.pca.G = np.dot(self.tabdata.scaled.T, incoming['h_global'])
        self.pca.S = np.linalg.norm(self.pca.G, axis=1)
        self.pca.H = incoming['h_global']
        self.pca.to_csv(self.left_eigenvector_file, self.right_eigenvector_file, self.eigenvalue_file)
        self.computation_done = True
        self.send_data = False

    def save_pca(self):
        # update PCA and save
        self.pca.to_csv(self.left_eigenvector_file, self.right_eigenvector_file, self.eigenvalue_file)
        self.computation_done = True
        self.send_data = False

    def orthogonalise_current(self, incoming):
        print('starting orthogonalise_current')
        self.global_conorms = incoming['global_conorms']
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
        self.all_global_eigenvector_norms.append(incoming['global_eigenvector_norm'])

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
        self.progress = 1.0
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
        self.out = {'local_h': self.pca.H}
        if self.federated_qr == QR.FEDERATED_QR:
            self.init_federated_qr()

    def init_approximate_pca(self):
        self.interation_counter = 0
        self.converged = False
        self.out = {'local_h': self.pca.H}
        if self.federated_qr == QR.FEDERATED_QR:
            self.init_federated_qr()

    def compute_h_local_g(self):
        self.update_progess()
        self.pca.H = np.dot(self.tabdata.scaled, self.pca.G)
        self.out = {'local_h': self.pca.H}
        return True

    def calculate_local_vector_conorms(self, incoming):
        vector_conorms = []
        # append the lastly calculated norm to the list of global norms
        self.all_global_eigenvector_norms.append(incoming['global_eigenvector_norm'])
        for cvi in range(self.current_vector):
            vector_conorms.append(np.dot(self.pca.G[:, cvi], self.pca.G[:, self.current_vector]) / self.all_global_eigenvector_norms[cvi])
        self.local_vector_conorms = vector_conorms
        if self.current_vector == self.k:
            self.orthonormalisation_done = True
        self.out = {'local_conorms': self.local_vector_conorms}
        return True

    def compute_local_eigenvector_norm(self):
        print('starting eigenvector norms')
        # not the euclidean norm, because the square root needs to be calculated
        # at the aggregator
        self.local_eigenvector_norm = np.dot(self.pca.G[:, self.current_vector],
                                  self.pca.G[:, self.current_vector])
        self.current_vector = self.current_vector + 1
        self.out = {'local_eigenvector_norm': self.local_eigenvector_norm}
        return True