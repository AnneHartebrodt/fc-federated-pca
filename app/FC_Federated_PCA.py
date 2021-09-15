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


    def next_state(self):
        self.state = self.step_queue.pop(0)
        return self.state

    def peek_next_state(self):
        try:
            return self.step_queue[0]
        except:
            print('No more states')

    def get_state(self):
        return self.get_state()

    def copy_configuration(self, config, directory):
        self.config_available = config.config_available
        self.batch = config.batch
        self.directories = config.directories
        self.input_file = op.join(INPUT_DIR, directory, config.input_file)
        self.left_eigenvector_file = op.join(OUTPUT_DIR, directory, config.left_eigenvector_file)
        self.right_eigenvector_file = op.join(OUTPUT_DIR, directory, config.right_eigenvector_file)
        self.eigenvalue_file = op.join(OUTPUT_DIR, directory, config.eigenvalue_file)
        self.projection_file = op.join(OUTPUT_DIR, directory, config.projection_file)
        self.k = config.k
        self.algorithm = config.algorithm
        self.federated_qr = config.federated_qr
        self.max_iterations = config.max_iterations
        self.epsilon = config.epsilon
        self.approximate_pca = config.approximate_pca
        self.init_method = config.init_method

        self.sep = config.sep
        self.has_rownames = config.has_rownames
        self.has_colnames = config.has_colnames
        self.federated_dimensions = config.federated_dimensions
        self.allow_transmission = config.allow_transmission
        self.encryption = config.encryption


    def read_input_files(self):
        try:

            self.tabdata = TabData.from_file(self.input_file, header=self.has_colnames,
                                             index=self.has_rownames, sep=self.sep)
            self.computation_done = True
        except Exception as e:
            print('[API] reading data failed')
            print(traceback.print_exc())


    def init_random(self):
        self.svd.pca = SVD.init_random(self.svd.tabdata, k=self.svd.k)
        return True

    def init_approximate(self):
        self.svd.pca = SVD.init_local_subspace(self.svd.tabdata, k=self.svd.k)
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

    def save_pca(self):
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
        print(self.projection_file)
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
        self.step_queue = self.step_queue + [Step.SAVE_SVD, Step.COMPUTE_PROJECTIONS, Step.SAVE_PROJECTIONS,
                                             Step.FINALIZE]

    def init_federated_qr(self):
        self.orthonormalisation_done = False
        self.current_vector = 0
        self.global_cornoms = []
        self.local_vector_conorms = []
        self.local_eigenvector_norm = -1
        self.all_global_eigenvector_norms = []





