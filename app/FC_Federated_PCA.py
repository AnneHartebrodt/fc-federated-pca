import yaml
import os
import re
import os.path as op
from app.params import INPUT_DIR, OUTPUT_DIR
from app.TabData import TabData

class FCFederatedPCA:
    def __init__(self, coordinator):
        self.step = 0
        self.tabdata = None
        self.SVD = None
        self.stage = 'init'
        self.config_available = False
        self.coordinator = coordinator
        self.out = None
        self.data_available = False

    def parse_configuration(self):
        print('[API] /setup parsing parameter file ')

        regex = re.compile('^config.*\.(yaml||yml)$')
        config_file = None
        files = os.listdir(INPUT_DIR)
        for file in files:
            if regex.match(file):
                print('[API] /setup config file found')
                config_file = file
                break
        if op.exists(op.join(INPUT_DIR, config_file)):
            self.config_available = True
            with open(op.join(INPUT_DIR, config_file), 'r') as file:
                parameter_list = yaml.load(file, Loader=yaml.FullLoader)
                parameter_list = parameter_list['fc_pca']
                # Files
                self.input_file = parameter_list['input']['data']

                # prepend mount folder
                self.eigenvalue_file =  op.join(OUTPUT_DIR, parameter_list['output']['eigenvalues'])
                self.left_eigenvector_file =  op.join(OUTPUT_DIR, parameter_list['output']['left_eigenvectors'])
                self.right_eigenvector_file =  op.join(OUTPUT_DIR, parameter_list['output']['right_eigenvectors'])
                self.projection_file =  op.join(OUTPUT_DIR, parameter_list['output']['projections'])
                self.scaled_data_file =  op.join(OUTPUT_DIR, parameter_list['output']['scaled_data'])


                self.k =  parameter_list['algorithm']['pcs']
                self.algorithm =  parameter_list['algorithm']['algorithm']
                self.federated_qr =  parameter_list['algorithm']['qr']
                self.eigenvector_update =  parameter_list['algorithm']['eigenvector_update']
                self.data_partioning = parameter_list['algorithm']['data_partitioning']
                self.max_iterations =  parameter_list['algorithm']['max_iterations']
                if parameter_list['settings']['rownames']:
                    self.has_rownames = True
                else:
                    self.has_rownames = False
                if parameter_list['settings']['colnames']:
                    self.has_colnames = True
                else:
                    self.has_colnames = False
                self.sep =  parameter_list['settings']['delimiter']
                self.allow_rerun = parameter_list['privacy']['allow_rerun']
                self.allow_transmission =  parameter_list['privacy']['allow_transmission']

                self.outlier_removal = parameter_list['privacy']['outlier_removal']
                self.encryption =  parameter_list['privacy']['encryption']

                # Fall back to local outlier removal
                if not self.allow_transmission and self.outlier_removal == 'global':
                    self.outlier_removal = 'local'

                self.finalize_parameter_setup()


                # No user interaction required, set available to true
                # master still sends configuration to all clients.
                if self.coordinator:
                    self.out = {'pcs': self.k,
                           'allow_rerun': self.allow_rerun,
                           'allow_transmission': self.allow_transmission,
                           'outlier_removal': self.outlier_removal}
                    self.data_available = True

        else:
            print('[API] /setup no configuration file found -- configure using user interface ')
            self.config_available = False

    def read_input_files(self):
        self.tabdata = TabData.from_file(self.input_file)


    def finalize_parameter_setup(self):
        return True

    def scale_data(self, means):
        self.tabdata.scaled = self.tabdata.data - means


    def save_scaled_data(self):
        saveme = pd.DataFrame(self.tabdata.scaled)
        saveme.columns = self.tabdata.columns
        saveme.rows = self.tabdata.rows
        saveme.to_csv(self.scaled_data_file, header=True, index=True, sep='\t')
        return True