from enum import Enum

class Step(Enum):
    LOAD_CONFIG = 'load_config'
    WAIT_FOR_PARAMS = 'wait_for_params'
    READ_DATA = 'read_data'
    COMPUTE_LOCAL_SUMS = 'compute_local_sums'
    COMPUTE_GLOBAL_MEANS =  'compute_global_means'
    SCALE_DATA = 'scale_data'
    COMPUTE_LOCAL_SUM_OF_SQUARES = 'compute_local_sum_of_squares'
    AGGREGATE_SUM_OF_SQUARES = 'aggregated_sum_of_squares'
    SCALE_TO_UNIT_VARIANCE = 'scale_to_unit_variance'
    FINALIZE = 'finalize'
