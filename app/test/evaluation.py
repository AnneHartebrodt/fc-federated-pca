import os
import gzip
import numpy
import scipy.linalg as la

import math
import scipy.linalg as la
import pandas as pd
import scipy.sparse.linalg as lsa
import numpy as np
from scipy.sparse import coo_matrix
import scipy as sc

def scale_center_data_columnwise(data, center=True, scale_variance=False):
    return scale_center_data(data, center, scale_variance)

def scale_center_data(data, center=True, scale_variance=False):
    """
    This function centers the data by subtracting the column menans. Scaling to equal variance
    is done by divinding the entries by the column standard deviation.
    :param data: nxd numpy array , containing n samples with d variables
    :param center: if true, data is centered by subtracting the column mean
    :param scale_variance: if true, data is scaled by dividing by the standard deviation
    :return: the scaled data
    """
    # data.dtype = 'float'
    data = data.astype('float')

    if scale_variance or center:
        for column in range(data.shape[1]):
            mean_val = sc.mean(data[:, column])
            var_val = math.sqrt(sc.var(data[:, column], ddof=1))
            for elem in range(len(data[:, column])):
                if center:
                    data[elem, column] = data[elem, column] - mean_val
                if scale_variance:
                    data[elem, column] = data[elem, column] / var_val

    return data

def angle(v1, v2):
    """
    Calculates the angle between to n-dimensional vectors
    and returns the result in degree. The angle returned
    can maximally be 90, otherwise the complement will be returned
    Args:
        v1: first vector
        v2: second vector

    Returns: angle in degree or NaN

    """
    dp = np.dot(v1, v2)
    norm_x = la.norm(v1)
    norm_y = la.norm(v2)
    co = np.clip(dp / (norm_x * norm_y), -1, 1)
    theta = np.arccos(co)
    a = math.degrees(theta)
    # angle can be Nan
    # print(angle)
    if math.isnan(a):
        return a
    # return the canonical angle
    if a > 90:
        return np.abs(a - 180)
    else:
        return a


def compute_angles(canonical, split, reported_angles=20):
    angles = list()
    for i in range(min(reported_angles, min(canonical.shape[1], split.shape[1]))):
        a = angle(canonical[:, i], split[:, i])
        angles.append(a)
    return angles

def compute_correlations(canonical, split, reported_angles=20):
    correlations = list()
    for i in range(min(reported_angles, min(canonical.shape[1], split.shape[1]))):
        c = np.corrcoef(canonical[:, i], split[:, i])
        correlations.append(c[0,1])
    return correlations


def read_and_concatenate_reference(file_list):
    ref_list = []
    for f in file_list:
        # read all original files
        ref0 = pd.read_csv(f, sep='\t', index_col=0)
        ref0 = ref0.values
        ref_list.append(ref0)
    ref = np.concatenate(ref_list, axis=1)
    ref = coo_matrix.asfptype(ref)
    return ref

def compute_reference_svd(ref):
    # Compute eigendecomposition
    u, s, v = lsa.svds(ref, k=10)

    v = np.flip(v.T, axis=1)
    u = np.flip(u, axis=1)
    s = np.flip(s)
    return u,s,v



def read_and_concatenate_eigenvectors(file_list):
    eigenvector_list=[]
    for f in file_list:
        eig0 = pd.read_csv(f, sep='\t', index_col=None, header=None)
        eig0 = eig0.values
        eigenvector_list.append(eig0)
    eig = np.concatenate(eigenvector_list, axis=0)

    return eig

def wrapper(file_list, eigen_file_list, center=True):
    ref = read_and_concatenate_reference(file_list)
    u, s, v = compute_reference_svd(ref)
    eig = read_and_concatenate_eigenvectors(eigen_file_list)
    # Compute angles
    angles = compute_angles(eig, v)
    return angles


if __name__ == '__main__':


    # MNIST fully federated
    file_list = ['/home/anne/Documents/featurecloud/apps/test_data/pca-test-mnist/0/mnist-test.tsv',
             '/home/anne/Documents/featurecloud/apps/test_data/pca-test-mnist/1/mnist-test.tsv',
                 '/home/anne/Documents/featurecloud/apps/test_data/pca-test-mnist/2/mnist-test.tsv']

    eig = read_and_concatenate_reference(file_list)

    eigen_file_list = ['/home/anne/Documents/featurecloud/test-environment/featurecloud-controller/fc_linux/results0/right_eigenvectors.tsv',
                   '/home/anne/Documents/featurecloud/test-environment/featurecloud-controller/fc_linux/results1/right_eigenvectors.tsv',
                       '/home/anne/Documents/featurecloud/test-environment/featurecloud-controller/fc_linux/results2/right_eigenvectors.tsv']

    ev = read_and_concatenate_eigenvectors(eigen_file_list)
    print(wrapper(file_list, eigen_file_list))
    #[0.0, 5.193302344775284e-06, 6.156649318399953e-06, 0.0006816712932220526, 0.0006817386574939947,
    #1.010198601586461e-05, 0.00015389018338396454, 0.05556583589213915, 0.05556562281765309, 5.998329526685641e-05]
    # MNIST partially federated

    eigen_file_list = ['/home/anne/Documents/featurecloud/dev/pca-tool/fed-pca-client/test_datasets/mnist/mnist_split_0.tsv_22.results',
                   '/home/anne/Documents/featurecloud/dev/pca-tool/fed-pca-client/test_datasets/mnist/mnist_split_1.tsv_22.results']

    print(wrapper(file_list, eigen_file_list))
    #[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.05682056669285989, 0.0568205666736219, 0.0]
