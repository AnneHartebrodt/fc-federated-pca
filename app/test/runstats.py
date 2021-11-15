import sys
sys.path.append('/home/anne/Documents/featurecloud/apps/fc-federated-pca/')

import app.PCA.shared_functions as sh
import app.PCA.comparison as co
import pandas as pd
import argparse as ap
import numpy as np
import os as os
import os.path as op
import yaml
import markdown
import app.PCA.markdown_utils as md

def summarize(files, ids, outfile):
    dfl  = []
    cols = []
    for f in files:
        df = pd.read_csv(f, sep='\t', header=None, index_col=None)
        dfl.append(df.iloc[:,1])
        cols = df.iloc[:,0].values
    df = pd.concat(dfl, axis=1)
    df = df.transpose().values
    ids = np.asarray(ids)
    ids = np.atleast_2d(ids).T
    df = np.concatenate([ids, df], axis=1)
    df = pd.DataFrame(df, dtype=float64)
    cols = np.concatenate([['Run ID'], cols])
    df.columns = cols
    df = df.round(2)
    df.to_csv(outfile, sep='\t', index = False)




if __name__ == '__main__':
    parser = ap.ArgumentParser(description='Split complete data into test data for federated PCA')
    parser.add_argument('-d', metavar='DIRECTORY', type=str, help='output directory', default='.')
    parser.add_argument('-o', metavar='OUTPUT', type=str, help='filename of evaluation output')
    parser.add_argument('-f', metavar='INPUT file list', type=str, nargs='+', help='config file')
    parser.add_argument('-i', metavar='INPUT ids', type=str, nargs='+', help='config file')

    args = parser.parse_args()
    basedir = args.d
    summarize(args.f, args.i, op.join(args.d, args.o))
