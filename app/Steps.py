from enum import Enum

class Step(Enum):
    LOAD_CONFIG = 'Loading configuration parameters'
    WAIT_FOR_PARAMS = 'Waiting for parameters'
    READ_DATA = 'Reading data'
    COMPUTE_H_LOCAL = 'Updating local eigenvectors'
    COMPUTE_G_LOCAL = 'Updating local left eigenvectors'
    AGGREGATE_H = 'Aggregating eigenvectors'
    INIT_POWER_ITERATION = 'Inititialising Power iteration'
    UPDATE_H = 'Updating local eigenvectors (no QR)'
    SAVE_SVD = 'Saving SVD'
    SAVE_SCALED_DATA = 'Saving scaled data'

    FINALIZE = 'Finalising'
    FINISHED = 'Finished'
    COMPUTE_PROJECTIONS = 'Computing projections'
    SAVE_PROJECTIONS = 'Saving projections'


    APPROXIMATE_LOCAL_PCA = 'Approximating local subspaces'
    AGGREGATE_SUBSPACES = 'Aggregating approx. subspaces'

    COMPUTE_COVARIANCE = 'Computing local covariance matrix'
    AGGREGATE_COVARIANCE = 'Aggregating covariance matrix'

    COMPUTE_QR = 'Computing local QR'
    AGGREGATE_QR = 'Aggregating R matrices'

    COMPUTE_LOCAL_NORM = 'Computing local norm'
    COMPUTE_LOCAL_CONORM = 'Computing local co-norm'
    AGGREGATE_NORM = 'Aggregating norms'
    AGGREGATE_CONORM = 'Aggregating co-norms'
    ORTHOGONALISE_CURRENT = "orthogonalising eigenvectors (federated QR)"
    NORMALISE_G = 'Normalising orthongonalised matrix'
