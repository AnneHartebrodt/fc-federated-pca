import sys
sys.path.append('/home/anne/Documents/featurecloud/apps/fc-federated-pca/')
from app.PCA.shared_functions import partition_data_horizontally
import os
import os.path as op
import pandas as pd
import numpy
import argparse as ap
import numpy as np


def make_horizontal_splits(input_file, output_folder, splits=3, seed = 11, batch=False):
    data = pd.read_csv(input_file, sep='\t', header=None, index_col=None)
    data = data.values
    data_list, choice = partition_data_horizontally(data, splits=splits)
    for i in range(splits):
        if batch:
            os.makedirs(op.join(output_folder, str(i), str(seed)), exist_ok=True)
            # basedir/data_splits/client/crossvalidation_split
            pd.DataFrame(data_list[i]).to_csv(op.join(output_folder, str(i), str(seed), 'test_data.tsv'), sep='\t', header=False, index=False)
        else:
            os.makedirs(op.join(output_folder, str(i)), exist_ok=True)
            # basedir/data_splits/client/crossvalidation_split
            pd.DataFrame(data_list[i]).to_csv(op.join(output_folder, str(i), 'test_data.tsv'), sep='\t',
                                              header=False, index=False)


if __name__ == '__main__':

    parser = ap.ArgumentParser(description='Split complete data into test data for federated PCA')
    parser.add_argument('-d', metavar='DIRECTORY', type=str, help='output directory', default='.')
    parser.add_argument('-f', metavar='INPUT_FILE', type=str, help='filename of data file')
    parser.add_argument('-n', metavar='SITES', type=int, help='Number of sites')
    parser.add_argument('-s', metavar='SEED', type=int, help='random seed', default=11)
    parser.add_argument('-b', metavar='BATCH', type=bool, help='batch mode', default=False)
    args = parser.parse_args()
    basedir = args.d
    output_folder = op.join(basedir, 'data_split')
    if not args.b:
        np.random.seed(args.s)
        input_file = op.join(basedir, 'data', args.f)
        make_horizontal_splits(input_file=input_file,
                               output_folder=output_folder,
                               splits=args.n,
                               seed=args.s,
                               batch=False)
    else:
        input_folders = os.listdir(op.join(basedir, 'data'))
        input_folders = [int(i) for i in input_folders]
        print(input_folders)
        for i in input_folders:
            input_file = op.join(basedir, 'data', str(i), args.f)
            make_horizontal_splits(input_file=input_file,
                                   splits=args.n,
                                   seed=str(i),
                                   output_folder=output_folder,
                                   batch=True)