from enum import Enum

class Step(Enum):
    LOAD_CONFIG = 'load_config'
    WAIT_FOR_PARAMS = 'wait_for_params'
    READ_DATA = 'read_data'
    COMPUTE_LOCAL_SUMS = 'compute_local_sums'
    COMPUTE_GLOBAL_MEANS =  'compute_global_means'
    SCALE_DATA = 'scale_data'
    SCALE_LOCALLY = 'scale_locally'
    COMPUTE_LOCAL_SUM_OF_SQUARES = 'compute_local_sum_of_squares'
    AGGREGATE_SUM_OF_SQUARES = 'aggregated_sum_of_squares'
    SCALE_TO_UNIT_VARIANCE = 'scale_to_unit_variance'
    COMPUTE_H_LOCAL = 'Compute H local'
    COMPUTE_G_LOCAL = 'Compute G local'
    AGGREGATE_H = 'Aggregate_H'
    ORTHONORMALISE_G = 'Orthonormalise G'
    INIT_POWER_ITERATION = 'Init power iteration'
    SAVE_SVD = 'Save_SVD'
    SAVE_SCALED_DATA = 'Save scaled data'
    WAIT_FOR_G = 'Wait for G'
    FINALIZE = 'finalize'
    FINISHED = 'finished'
    SHOW_RESULT = 'show result'
    COMPUTE_PROJECTIONS = 'compute_projections'
    SAVE_PROJECTIONS = 'save_projections'
    SAVE_OUTLIERS = 'Save outliers'
    INIT_RERUN = 'INIT_RERUN'


    COMPUTE_LOCAL_NORM = 'Compute local norm'
    COMPUTE_LOCAL_CONORM = 'Compute local conorm'
    AGGREGATE_NORM = 'Aggregate norm'
    AGGREGATE_CONORM = 'Aggregate Conorm'
    ORTHOGONALISE_CURRENT = "orthogonalise current"
    NORMALISE_G = 'Normalise orthongonal matrix'

    COMPUTING = 'COMPUTINg'