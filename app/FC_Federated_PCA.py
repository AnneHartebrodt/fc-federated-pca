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
        self.step_queue = [Step.LOAD_CONFIG] # this is the initial step queue
        self.state = 'waiting_for_start' # this is the inital state
        self.iteration_counter = 0
        self.converged = False


    def next_state(self):
        self.state = self.step_queue.pop(0)
        return self.state

    def get_state(self):
        return self.get_state()

    def parse_configuration(self):
        print('[API] /setup parsing parameter file ')

        regex = re.compile('^config.*\.(yaml||yml)$')
        config_file = "ginger_tea.txt"
        # check input dir for config file
        files = os.listdir(INPUT_DIR)
        for file in files:
            if regex.match(file):
                config_file = op.join(INPUT_DIR, file)
                break
        #check output dir for config file
        files = os.listdir(OUTPUT_DIR)
        for file in files:
            if regex.match(file):
                config_file = op.join(OUTPUT_DIR, file)
                break
        if op.exists(config_file):
            print('[API] /setup config file found ... parsing')
            self.config_available = True
            with open(op.join(INPUT_DIR, config_file), 'r') as file:
                parameter_list = yaml.load(file, Loader=yaml.FullLoader)
                parameter_list = parameter_list['fc_pca']
                # Files
                self.input_file = op.join(INPUT_DIR, parameter_list['input']['data'])

                # prepend mount folder
                self.eigenvalue_file =  op.join(OUTPUT_DIR, parameter_list['output']['eigenvalues'])
                self.left_eigenvector_file =  op.join(OUTPUT_DIR, parameter_list['output']['left_eigenvectors'])
                self.right_eigenvector_file =  op.join(OUTPUT_DIR, parameter_list['output']['right_eigenvectors'])
                self.projection_file =  op.join(OUTPUT_DIR, parameter_list['output']['projections'])
                self.scaled_data_file =  op.join(OUTPUT_DIR, parameter_list['output']['scaled_data'])

                print('files')

                self.k =  parameter_list['algorithm']['pcs']
                self.algorithm =  parameter_list['algorithm']['algorithm']
                self.federated_qr = parameter_list['algorithm']['qr']
                self.max_iterations = parameter_list['algorithm']['max_iterations']
                if parameter_list['settings']['rownames']:
                    self.has_rownames = True
                else:
                    self.has_rownames = False
                if parameter_list['settings']['colnames']:
                    self.has_colnames = True
                else:
                    self.has_colnames = False
                self.sep =  parameter_list['settings']['delimiter']

                print('algo settings')
                print(parameter_list['scaling'])
                self.center = parameter_list['scaling']['center']
                self.scale_variance = parameter_list['scaling']['scale_variance']
                self.transform = parameter_list['scaling']['transform']


                print('scaling')
                self.allow_rerun = parameter_list['privacy']['allow_rerun']
                self.allow_transmission = parameter_list['privacy']['allow_transmission']

                self.outlier_removal = parameter_list['privacy']['outlier_removal']
                self.encryption = parameter_list['privacy']['encryption']
                self.show_result = parameter_list['privacy']['show_result']

                # Fall back to local outlier removal
                if not self.allow_transmission and self.outlier_removal == 'global':
                    self.outlier_removal = 'local'

                print('[API] /setup config file found ... parsing done')

        else:
            print('[API] /setup no configuration file found -- configure using user interface ')
            self.config_available = False

    def read_input_files(self):
        try:

            self.tabdata = TabData.from_file(self.input_file, header = self.has_colnames,
                                             index=self.has_rownames, sep=self.sep)
            self.computation_done = True
        except Exception as e:
            print('[API] reading data failed')
            print(traceback.print_exc())

    def scale_data(self, incoming):
        try:
            means = incoming['means']
            self.tabdata.scaled = self.tabdata.data - means
            self.computation_done = True
            self.send_data = False
        except Exception as e:
            print('[API] scaling data failed')
            traceback.print_exc()
        return True

    def scale_data_to_unit_variance(self, incoming):
        try:
            vars = incoming['vars']
            self.tabdata.scaled = self.tabdata.data/vars
            self.computation_done = True
            self.send_data = False
        except Exception as e:
            print('[API] scaling data failed')
            traceback.print_exc()

    def set_parameters(self, incoming):
        try:
            print('[API] setting parameters')
            self.k = incoming['pcs']
            self.allow_rerun = incoming['allow_rerun']
            self.allow_transmission = incoming['allow_transmission']
            self.outlier_removal = incoming['outlier_removal']
            self.computation_done = True
        except Exception as e:
            print('[API] setting parameters failed')
            traceback.print_exc()
        return True

    def save_scaled_data(self):
        saveme = pd.DataFrame(self.tabdata.scaled)
        saveme.columns = self.tabdata.columns
        saveme.rows = self.tabdata.rows
        saveme.to_csv(self.scaled_data_file, header=True, index=True, sep='\t')
        self.computation_done = True
        self.send_data = False
        return True

    def save_pca(self):
        self.pca.to_csv(self.left_eigenvector_file,self.right_eigenvector_file, self.eigenvalue_file)
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
        self.pca.projections = np.dot(self.tabdata.scaled.T, self.pca.H)
        self.computation_done = True
        self.send_data = False

    def save_projections(self):
        self.pca.save_projections(self.projection_file, sep=self.sep)
        self.computation_done = True
        self.send_data = False



