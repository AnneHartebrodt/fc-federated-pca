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

def write_markdown_report(basedir, report):
    files = os.listdir(basedir)
    fl = []
    print(files)
    for f in files:
        fl.append(pd.read_csv(op.join(basedir, f), sep='\t', engine='python', header=0, index_col=None))
    table = pd.concat(fl)

    mdr = md.df_to_markdown(table)
    with open(report, 'w') as handle:
        handle.write('# Test report\n')
        handle.write(mdr)

if __name__ == '__main__':
    parser = ap.ArgumentParser(description='Split complete data into test data for federated PCA')
    parser.add_argument('-d', metavar='DIRECTORY', type=str, help='input the report directory', default='.')
    parser.add_argument('-r', metavar='REPORT', type=str, help='report as markdown', default='.')
    args = parser.parse_args()
    basedir = args.d

    write_markdown_report(basedir, args.r)


