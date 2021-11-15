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



def create_result(left_angles, right_angles,  config, run_id='NA', config_path='NA', result_path='NA'):
    l = []
    names = []
    names.append('Run ID')
    l.append(run_id)

    #names.append('Config file')
    #l.append(config_path)

    #names.append('Files')
    #l.append(result_path)
    for key in config:
        names.append(key)
        l.append(config[key])
    for a in range(len(left_angles)):
        names.append('LSV'+str(a+1))
        l.append(left_angles[a])
    for a in range(len(right_angles)):
        names.append('RSV'+str(a+1))
        l.append(right_angles[a])
    data = pd.DataFrame(l).T
    data.columns = names
    return data




if __name__ == '__main__':
    parser = ap.ArgumentParser(description='Split complete data into test data for federated PCA')
    parser.add_argument('-d', metavar='DIRECTORY', type=str, help='output directory', default='.')
    parser.add_argument('-l', metavar='left eigenvectors', type=str, help='filenames left eigenvectors (only 1)')
    parser.add_argument('-r', metavar='right eigenvectors', type=str, help='filename right eigenvectors ', nargs='+')
    parser.add_argument('-L', metavar='CANONICAL', type=str, help='filename of canonical left solution')
    parser.add_argument('-R', metavar='CANONICAL', type=str, help='filename of canonical right solution')
    parser.add_argument('-o', metavar='OUTPUT', type=str, help='filename of evaluation output')
    parser.add_argument('-e', metavar='CONFIG', type=str, help='config file')
    args = parser.parse_args()
    basedir = args.d


    os.makedirs(op.join(basedir, 'test_results'), exist_ok=True)
    federated_eigenvectors = pd.read_csv(args.l, header=None, index_col=None, sep='\t').values
    canconical_eigenvectors = pd.read_csv(args.L, header=None, index_col=None, sep='\t').values
    left_angles = co.compute_angles(federated_eigenvectors, canconical_eigenvectors)
    left_angles = [np.round(a, 2) for a in left_angles]

    federated_eigenvectors = read_and_concatenate_eigenvectors(args.r)
    print(federated_eigenvectors.shape)
    canconical_eigenvectors = pd.read_csv(args.R, header=None, index_col=None, sep='\t').values
    print(canconical_eigenvectors.shape)
    right_angles = co.compute_angles(federated_eigenvectors, canconical_eigenvectors)
    right_angles = [np.round(a, 2) for a in right_angles]

    config = read_config(configfile=args.e)
    ouput_table = create_result(left_angles, right_angles, config['fc_pca']['algorithm'],
                                run_id=args.o,
                                config_path=args.e,
                                result_path = args.R
                                )
    ouput_table.to_csv(op.join(op.join(basedir, 'test_results', args.o)), sep='\t', index=False)







