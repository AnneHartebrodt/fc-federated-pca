from app.FC_Federated_PCA import FCFederatedPCA
import  numpy as np
from app.Steps import Step

class AggregatorFCFederatedPCA(FCFederatedPCA):
    def __init__(self):
        self.dummy = None
        self.coordinator = True
        FCFederatedPCA.__init__(self)

    def finalize_parameter_setup(self):
        self.step_queue = self.step_queue + [Step.WAIT_FOR_PARAMS, Step.READ_DATA, Step.COMPUTE_LOCAL_SUMS, Step.COMPUTE_GLOBAL_MEANS,
                                             Step.SCALE_DATA,
                                             Step.COMPUTE_LOCAL_SUM_OF_SQUARES, Step.AGGREGATE_SUM_OF_SQUARES,
                                             Step.SCALE_TO_UNIT_VARIANCE, Step.FINALIZE]

        # No user interaction required, set available to true
        # master still sends configuration to all clients.
        self.out = {'pcs': self.k,
                    'allow_rerun': self.allow_rerun,
                    'allow_transmission': self.allow_transmission,
                    'outlier_removal': self.outlier_removal}
        self.send_data = True
        self.computation_done = True
        print('[API] [COORDINATOR] /setup config done!')
        # if self.algorithm == 'power_iteration':
        #     self.step_queue = ['agree_on_row_names', 'normalize', 'init_power_iteration']
        # else:
        #     self.step_queue = ['normalize', 'pca']

        
    def compute_local_sums(self):
        sums = np.sum(self.tabdata.data, axis=0)
        outdata = {'sums': sums, 'sample_count': self.tabdata.row_count}
        # Difference to the client: Do not set available to true.
        # Data is not to be sent
        self.out = outdata
        self.computation_done = True
        return True

    def compute_global_means(self, data):
        print(data)
        means = np.zeros(data[0]['sums'].shape)
        total_count = 0
        print(means)
        for d in data:
            total_count += d['sample_count']
            means = np.sum([means, d['sums']], axis=0)
        means = means/total_count
        print(means)
        self.out = {'means': means}
        self.computation_done = True
        self.send_data = True
        return True

    def compute_local_sum_of_squares(self):
        vars = np.sum(np.square(self.tabdata.data), axis=0)
        outdata = {'sums': vars, 'sample_count': self.tabdata.row_count}
        self.out = outdata
        self.computation_done = True
        return True

    def compute_global_sum_of_squares(self, incoming):
        vars = np.zeros(incoming[0]['sums'].shape)
        total_count = 0
        for d in incoming:
            vars = np.sum([vars, d['sums']], axis = 0)
            total_count = total_count + d['sample_count']
        vars = vars / (total_count - 1)
        vars = np.sqrt(vars)
        self.out = {'vars': vars}
        self.computation_done = True
        self.send_data = True
        return True
