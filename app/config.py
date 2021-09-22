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

class FCConfig:
    def __init__(self):

        self.config_available = False
        self.batch = False
        self.directories = []
        self.input_file = None
        self.left_eigenvector_file = None
        self.right_eigenvector_file = None
        self.projection_file = None
        self.k = 10
        self.algorithm = 'power_iteration'
        self.federated_qr = False
        self.max_iterations = 500
        self.epsilon = 10e-9
        self.approximate_pca =None
        self.init_method = 'approximate_pca'

        self.sep = '\t'
        self.has_rownames = False
        self.has_colnames = False
        self.federated_dimensions = 'row'
        self.allow_transmission = False
        self.encryption = False


    def parse_configuration(self):
        print('[API] /setup parsing parameter file ')
        regex = re.compile('^config.*\.(yaml||yml)$')
        config_file = "ginger_tea.txt"
        # check input dir for config file
        files = os.listdir(INPUT_DIR)
        for file in files:
            if regex.match(file):
                config_file = op.join(INPUT_DIR, file)
                config_out = op.join(OUTPUT_DIR, file)
                break
        # check output dir for config file
        files = os.listdir(OUTPUT_DIR)
        for file in files:
            if regex.match(file):
                config_file = op.join(OUTPUT_DIR, file)
                break
        if op.exists(config_file):
            # Copy file to output folder
            print('[API] /setup config file found ... parsing file: ' + str(op.join(INPUT_DIR, config_file)))
            copyfile(config_file, config_out)

            self.config_available = True
            with open(config_file, 'r') as file:
                parameter_list = yaml.safe_load(file)
                parameter_list = parameter_list['fc_pca']

                self.batch = parameter_list['input']['batch']
                print(self.batch)
                if self.batch:
                    print('CONFIG: BATCH Mode')
                    folders = os.listdir(INPUT_DIR)
                    for f in folders:
                        if op.isdir(op.join(INPUT_DIR, f)):
                            self.directories.append(f)
                            os.makedirs(op.join(OUTPUT_DIR, f), exist_ok=True)
                # Files
                try:
                    self.input_file = parameter_list['input']['data']
                except KeyError:
                    print('YAML file does not follow specification: missing key '+ str('data'))
                    raise KeyError

                # prepend mount folder
                try:
                    self.eigenvalue_file = parameter_list['output']['eigenvalues']
                except KeyError:
                    print('YAML file does not follow specification: missing key: eigenvalues')
                    print('Setting default: eigenvalues.tsv')
                    self.eigenvalue_file = 'eigenvalues.tsv'

                try:
                    self.left_eigenvector_file =   parameter_list['output']['left_eigenvectors']
                except KeyError:
                    print('YAML file does not follow specification: missing key: left_eigenvectors')
                    print('Setting default: left_eigenvectors.tsv')
                    self.left_eigenvector_file ='left_eigenvectors.tsv'

                try:
                    self.right_eigenvector_file =   parameter_list['output']['right_eigenvectors']
                except KeyError:
                    print('YAML file does not follow specification: missing key: right_eigenvectors')
                    print('Setting default: right_eigenvectors.tsv')
                    self.right_eigenvector_file = 'right_eigenvectors.tsv'

                try:
                    self.projection_file =   parameter_list['output']['projections']
                except KeyError:
                    print('YAML file does not follow specification: missing key: projections')
                    print('Setting default: projections.tsv')
                    self.projection_file =  'projections.tsv'

                try:
                    self.k =  parameter_list['algorithm']['pcs']
                    self.algorithm =  parameter_list['algorithm']['algorithm']
                    self.federated_qr = QR.from_str(parameter_list['algorithm']['qr'])
                    self.max_iterations = parameter_list['algorithm']['max_iterations']
                    self.epsilon = float(parameter_list['algorithm']['epsilon'])
                    self.approximate_pca = parameter_list['algorithm']['approximate_pca']
                    self.init_method = parameter_list['algorithm']['init']
                except KeyError:
                    print('YAML file does not follow specification: algorithm settings: algorithm')
                    raise KeyError

                try:
                    self.sep = parameter_list['settings']['delimiter']
                    self.has_rownames = parameter_list['settings']['rownames']
                    self.has_colnames = parameter_list['settings']['colnames']
                    self.federated_dimensions = parameter_list['settings']['federated_dimension']
                except KeyError:
                    print('YAML file does not follow specification: settings')
                    raise KeyError

                try:
                    self.allow_transmission = parameter_list['privacy']['allow_transmission']
                    self.encryption = parameter_list['privacy']['encryption']
                except KeyError:
                    print('YAML file does not follow specification: privacy settings')
                    raise KeyError

                print('[API] /setup config file found ... parsing done')

        else:
            print('[API] /setup no configuration file found -- configure using user interface ')
            self.config_available = False