import app.TabData as TabData
import app.SVD as SVD
import numpy as np
from app.FC_Federated_PCA import FCFederatedPCA
import pandas as pd

class ClientFCFederatedPCA(FCFederatedPCA):
    def __init__(self):
        self.dummy = None
        self.state = 'init'
        self.step_queue = ['load_config']

    def next_state(self):
        self.state = self.step_queue.pop(0)
        return self.state

    def get_state(self):
        return self.get_state()


    def finalize_parameter_setup(self):
        self.step_queue = self.step_queue + ['read_data', 'scale_data', 'finalize']
        # if self.algorithm == 'power_iteration':
        #     self.step_queue = ['init_algorithm', 'agree_on_row_names', 'init_power_iteration']
        # else:
        #     self.step_queue = ['init_algorithm', 'pca']

    def compute_local_sums(self):
        sums = np.sum(self.tabdata.data, axis=0)
        self.out = sums
        self.data_available = True
        return True



#def scale_datasets(data_list):
    # sums = []
    # sample_count = 0
    #
    # # mean
    # sums = [np.sum(d, axis = 0) for d in data_list]
    # sums = np.sum(sums, axis=0)
    # sample_count = [d.shape[0] for d in data_list]
    # total_count = sum(sample_count)
    # means = [s/total_count for s in sums]
    # for i in range(len(data_list)):
    #     data_list[i] = data_list[i] - means
    #
    # #variance
    #
    # vars = [np.sum(np.square(d), axis=0) for d in data_list]
    # vars = np.sum(vars, axis = 0)
    # vars = vars/(total_count-1)
    # # variance  = 0
    # delete = np.where(vars==0)
    # vars = np.delete(vars, delete)
    # for i in range(len(data_list)):
    #     data_list[i] = np.delete(data_list[i], delete, axis=1)
    #
    # for i in range(len(data_list)):
    #     data_list[i] = data_list[i]/np.sqrt(vars)
    # return data_list