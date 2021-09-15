from app.PCA.shared_functions import partition_data_horizontally
import os
import os.path as op
import pandas as pd
import numpy


def make_horizontal_splits(basedir, dataset):
    data = pd.read_csv(op.join(basedir, dataset), sep='\t', header=0, index_col=0)
    data = data.values
    data_list, choice = partition_data_horizontally(data, splits=3)
    for i in range(splits):
        os.makedirs(op.join(basedir, str(i)))
        pd.DataFrame(data_list[i]).to_csv(op.join(basedir, str(i), 'test_data.tsv'), sep='\t')

if __name__ == '__main__':

    basedir = '/home/anne/Documents/featurecloud/apps/fc-federated-pca/app/test/test_data/'
    splits = 3
    dataset = 'test_data_full.tsv'
    config = make_horizontal_splits(basedir, dataset)