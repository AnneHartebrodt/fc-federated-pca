from enum import Enum
from app.Steps import Step
# communication parameters
class COParams(Enum):

    def __init__(self, name, smpc):
        self.n = name
        self.smpc = smpc

    @staticmethod
    def from_str(string_value):
        if string_value == 'H global':
            return COParams.H_GLOBAL
        elif string_value == 'H local':
            return COParams.H_LOCAL
        elif string_value =='Step':
            return COParams.STEP
        elif string_value == 'finished':
            return COParams.FINISHED
        elif string_value == 'Covariance matrix':
            return COParams.COVARIANCE_MATRIX
        elif string_value == 'Global Cornorms':
            return COParams.GLOBAL_CORNORMS
        elif string_value == 'Local Conorms':
            return COParams.LOCAL_CONORMS
        elif string_value == 'Global Eigenvector norm':
            return COParams.GLOBAL_EIGENVECTOR_NORM
        elif string_value == 'Local Eigenvector norm':
            return COParams.LOCAL_EIGENVECTOR_NORM
        elif string_value == 'R':
            return COParams.R
        elif string_value == 'Orthonormalisation done':
            return COParams.ORTHONORMALISATION_DONE
        elif string_value == 'PCs':
            return COParams.PCS
        elif string_value == 'Converged':
            return COParams.CONVERGED
        else:
            return None

    @staticmethod
    def to_step(string_value):
        if string_value == 'H local':
            return Step.UPDATE_H
        elif string_value == 'Covariance matrix':
            return Step.COMPUTE_COVARIANCE
        else:
            return None



    H_GLOBAL = 'H global', False
    H_LOCAL = 'H local', True
    STEP = 'Step', False
    FINISHED = 'finished', False
    COVARIANCE_MATRIX = 'Covariance matrix', True
    GLOBAL_CORNORMS = 'Global Cornorms', False
    LOCAL_CONORMS = 'Local Conorms', True
    GLOBAL_EIGENVECTOR_NORM = 'Global Eigenvector norm', False
    LOCAL_EIGENVECTOR_NORM = 'Local Eigenvector norm', True
    R = 'R', False
    CONVERGED = 'Converged', False
    ORTHONORMALISATION_DONE = 'Orthonormalisation done', False
    PCS = 'PCs', False


