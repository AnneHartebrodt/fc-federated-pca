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



def read_and_concatenate_eigenvectors(file_list):
    eigenvector_list=[]
    for f in file_list:
        eig0 = pd.read_csv(f, sep='\t', index_col=None, header=None)
        eig0 = eig0.values
        eigenvector_list.append(eig0)
    eig = np.concatenate(eigenvector_list, axis=0)
    return eig

def read_config(configfile):
    with open(op.join(configfile), 'r') as handle:
        config = yaml.safe_load(handle)
    return config



def create_result(angles, config):
    l = []
    names = []
    for key in config:
        names.append(key)
        l.append(config[key])
    for a in range(len(angles)):
        names.append('EV'+str(a+1))
        l.append(angles[a])
    data = pd.DataFrame(l).T
    data.columns = names
    return data




if __name__ == '__main__':
    parser = ap.ArgumentParser(description='Split complete data into test data for federated PCA')
    parser.add_argument('-d', metavar='DIRECTORY', type=str, help='output directory', default='.')
    parser.add_argument('-f', metavar='FILES', type=str, help='filenames of output files', nargs='+')
    parser.add_argument('-c', metavar='CANONICAL', type=str, help='filename of canonical solution')
    parser.add_argument('-o', metavar='OUTPUT', type=str, help='filename of evaluation output')
    parser.add_argument('-e', metavar='CONFIG', type=str, help='config file')
    args = parser.parse_args()
    basedir = args.d

    print(args.f)
    os.makedirs(op.join(basedir, 'test_results'), exist_ok=True)
    federated_eigenvectors = read_and_concatenate_eigenvectors(args.f)
    canconical_eigenvectors = pd.read_csv(args.c, header=None, index_col=None, sep='\t').values[0:3750, :]
    angles = co.compute_angles(federated_eigenvectors, canconical_eigenvectors)
    config = read_config(configfile=args.e)
    ouput_table = create_result(angles, config['fc_pca']['algorithm'])
    ouput_table.to_csv(op.join(op.join(basedir, 'test_results', args.o)), sep='\t', index=False)







