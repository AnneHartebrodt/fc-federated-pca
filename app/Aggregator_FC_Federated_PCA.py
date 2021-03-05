from app.FC_Federated_PCA import FCFederatedPCA
import  numpy as np

class AggregatorFCFederatedPCA(FCFederatedPCA):
    def __init__(self):
        self.dummy = None

    def finalize_parameter_setup(self):
        self.step_queue = self.step_queue + ['read_data', 'scale_data', 'finalize']
        # if self.algorithm == 'power_iteration':
        #     self.step_queue = ['agree_on_row_names', 'normalize', 'init_power_iteration']
        # else:
        #     self.step_queue = ['normalize', 'pca']

        
    def compute_local_sums(self):
        sums = np.sum(self.tabdata, axis=0)