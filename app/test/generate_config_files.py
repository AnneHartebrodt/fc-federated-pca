import yaml
import os.path as op
import os
import argparse as ap


def make_default_config_file(algorithm = 'power_iteration',
                             qr='no_qr',
                             init = 'approximate_pca',
                             batch=False,
                             train_test=False,
                             maxit=500,
                             use_smpc = True):

    """
    Default config file generator
    qr: one of 'federated_qr'| 'no_qr'
    :return:
    """
    dict = {'fc_pca':
             {'input':
                  {'data': 'data.tsv',
                   'batch': batch,
                   'train_test': train_test},
              'output':
                  {'projections': 'reduced_data.tsv',
                   'left_eigenvectors': 'left_eigenvectors.tsv',
                   'right_eigenvectors': 'right_eigenvectors.tsv',
                   'eigenvalues': 'eigenvalues.tsv'},
              'algorithm':
                  {'pcs': 10,
                   'algorithm': algorithm,
                   'max_iterations': maxit,
                   'qr': qr,
                   'epsilon': 1e-12,
                   'init': init
                   },
              'settings':
                  {'delimiter': '\t',
                   'rownames': False,
                   'colnames': False},
              'privacy':
                  {'allow_transmission': False,
                   'encryption': 'no_encryption',
                   'use_smpc': use_smpc}
              }
            }
    return dict

def write_config(config, basedir, counter):
    os.makedirs(op.join(basedir,  str(counter)), exist_ok=True)
    with open(op.join(basedir,  str(counter), 'config.yaml'), 'w') as handle:
        yaml.safe_dump(config, handle, default_flow_style=False, allow_unicode=True)


def create_configs_power(output_folder, batch=False, train_test=False, maxit=500,     qr = ['federated_qr', 'no_qr'],
                         init=['approximate_pca', 'random'], use_smpc=[True, False]):

    counter = 0
    for q in qr:
        for i in init:
            for s in use_smpc:
                config = make_default_config_file(batch=batch,
                                                  algorithm='power_iteration',
                                                  qr=q,
                                                  init=i,
                                                  train_test=train_test,
                                                  maxit=maxit,
                                                  use_smpc=s)
                write_config(config=config, basedir=output_folder, counter=counter)
                counter = counter + 1
    return counter

def create_configs_single_round(output_folder, count, batch=True, train_test=True, maxit=500, use_smpc=[True, False]):
    counter = count
    for a in ['approximate_pca', 'full_covariance','qr_pca']:
        for s in use_smpc:
            config = make_default_config_file(batch=batch, algorithm=a, train_test=train_test, maxit=maxit, use_smpc=s)
            write_config(config=config, basedir=output_folder, counter=str(counter))
            counter = counter+1

if __name__ == '__main__':
    parser = ap.ArgumentParser(description='Split complete data into test data for federated PCA')
    parser.add_argument('-d', metavar='DIRECTORY', type=str, help='output directory', default='.')
    parser.add_argument('-b', metavar='BATCH', type=bool, help='batch mode', default=False)
    parser.add_argument('-t', metavar='TRAIN_TEST', type=bool, help='batch mode', default=False)
    parser.add_argument('-s', metavar='USE SMPC', type=bool, help='batch mode', default=True)
    parser.add_argument('-o', metavar='OUTPUT_DIRECTORY_NAME', type=str, help='output directory', default='.')
    args = parser.parse_args()
    basedir = args.d

    output_folder = op.join(basedir, args.o, 'config_files')
    os.makedirs(output_folder, exist_ok=True)
    count = create_configs_power(output_folder, batch=args.b, train_test=args.t, maxit=5, qr=['no_qr', 'federated_qr'], use_smpc=[True, False])
    create_configs_single_round(output_folder, count, batch=args.b, train_test= args.t, maxit=5,use_smpc=[True, False])




