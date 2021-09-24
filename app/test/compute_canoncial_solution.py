import sys
sys.path.append('/home/anne/Documents/featurecloud/apps/fc-federated-pca/')
import numpy as np
import scipy as sc
import pandas as pd
import scipy.sparse.linalg as la
import os
import argparse as ap
import os.path as op
import app.PCA.shared_functions as sh

def compute_and_save_canonical(input_file, output_folder,k=10, seed = 11, prefix='singular'):
    np.random.seed(seed)
    data = pd.read_csv(input_file, sep='\t')
    data = data.values
    u, s, v, nd = sh.svd_sub(data, ndims=k)

    os.makedirs(output_folder, exist_ok=True)
    pd.DataFrame(u).to_csv(op.join(output_folder, prefix + '.right'), sep='\t', header=False, index=False)
    pd.DataFrame(s).to_csv(op.join(output_folder, prefix + '.values'), sep='\t', header=False, index=False)
    pd.DataFrame(v).to_csv(op.join(output_folder, prefix + '.left'), sep='\t', header=False, index=False)


if __name__ == '__main__':
    parser = ap.ArgumentParser(description='Generate sample data for federated PCA')
    parser.add_argument('-d', metavar='DIRECTORY', type=str, help='output directory', default='.')
    parser.add_argument('-f', metavar='INPUT_FILE', type=str, help='filename of data file')
    parser.add_argument('-o', metavar='OUTPUT_FILE', type=str, help='output file prefix', default='eigen')
    parser.add_argument('-k', metavar='K', type=int, help='Number of samples')
    parser.add_argument('-s', metavar='SEED', type=int, help='random seed', default=11)
    parser.add_argument('-b', metavar='BATCH', type = bool, help='batch mode', default=False)
    args = parser.parse_args()
    basedir = args.d
    output_folder = op.join(args.d, 'baseline_results')

    if args.b:
        input_folders = os.listdir(op.join(basedir, 'data'))
        input_folders = [int(i) for i in input_folders]
        for i in input_folders:
            output_folder = op.join(basedir, 'baseline_result', str(i))
            input_file = op.join(basedir, 'data', str(i), args.f)
            compute_and_save_canonical(input_file=input_file,
                                       output_folder=output_folder,
                                       seed=i,
                                       prefix=args.o,
                                       k=args.k)
    else:
        output_folder = op.join(basedir, 'baseline_result')
        input_file = op.join(basedir, 'data', args.f)
        compute_and_save_canonical(input_file=input_file,
                                   output_folder=output_folder,
                                   seed=args.s,
                                   prefix=args.o,
                                   k=args.k)

