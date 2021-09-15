from enum import Enum

class Step(Enum):
    LOAD_CONFIG = 'load_config'
    WAIT_FOR_PARAMS = 'wait_for_params'
    READ_DATA = 'read_data'
    COMPUTE_H_LOCAL = 'Compute H local'
    COMPUTE_G_LOCAL = 'Compute G local'
    AGGREGATE_H = 'Aggregate_H'
    INIT_POWER_ITERATION = 'Init power iteration'
    UPDATE_H = 'Update H'
    SAVE_SVD = 'Save_SVD'
    SAVE_SCALED_DATA = 'Save scaled data'

    FINALIZE = 'finalize'
    FINISHED = 'finished'
    COMPUTE_PROJECTIONS = 'compute_projections'
    SAVE_PROJECTIONS = 'save_projections'
    SAVE_OUTLIERS = 'Save outliers'
    INIT_RERUN = 'INIT_RERUN'

    APPROXIMATE_LOCAL_PCA = 'APPROXIMATE_LOCAL_PCA'
    AGGREGATE_SUBSPACES = 'AGGREGATE_SUBSPACES'


    COMPUTE_LOCAL_NORM = 'Compute local norm'
    COMPUTE_LOCAL_CONORM = 'Compute local conorm'
    AGGREGATE_NORM = 'Aggregate norm'
    AGGREGATE_CONORM = 'Aggregate Conorm'
    ORTHOGONALISE_CURRENT = "orthogonalise current"
    NORMALISE_G = 'Normalise orthongonal matrix'

    COMPUTING = 'COMPUTING'