import yaml
import os.path as op
import os
import argparse as ap


def make_default_config_file(algorithm = 'power_iteration',
                             qr='no_qr',
                             init = 'random',
                             batch=False,
                             train_test=False,
                             maxit=500,
                             use_smpc = True,
                             datafile = 'data.tsv'):

    """
    Default config file generator
    qr: one of 'federated_qr'| 'no_qr'
    :return:
    """
    dict = {'fc_pca':
             {'input':
                  {'data': datafile,
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
                   'epsilon': 1e-9,
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
                         init=['approximate_pca', 'random'], use_smpc=[True, False], datafile='data.tsv'):

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
                                                  use_smpc=s,
                                                  datafile=datafile)
                write_config(config=config, basedir=output_folder, counter=counter)
                counter = counter + 1
    return counter

def create_configs_single_round(output_folder, count, batch=True, train_test=True, maxit=500, use_smpc=[True, False], datafile='data.tsv'):
    counter = count
    for a in ['approximate_pca', 'full_covariance','qr_pca']:
        for s in use_smpc:
            config = make_default_config_file(batch=batch, algorithm=a, train_test=train_test, maxit=maxit, use_smpc=s,
                                              datafile=datafile)
            write_config(config=config, basedir=output_folder, counter=str(counter))
            counter = counter+1

if __name__ == '__main__':
    parser = ap.ArgumentParser(description='Split complete data into test data for federated PCA')
    parser.add_argument('-d', metavar='DIRECTORY', type=str, help='output directory', default='.')
    parser.add_argument('-b', metavar='BATCH', type=bool, help='batch mode', default=False)
    parser.add_argument('-t', metavar='TRAIN_TEST', type=bool, help='batch mode', default=False)
    parser.add_argument('-s', metavar='USE SMPC', type=int, help='0 = no, 1=yes, 2=both', default=0)
    parser.add_argument('-o', metavar='OUTPUT_DIRECTORY_NAME', type=str, help='output directory', default='.')
    parser.add_argument('-i', metavar='ITERATIONS', type=int, help='number of iteratins', default=1000)
    parser.add_argument('-q', metavar='FEDERATED QR', type=int, help='0=no, 1=yes, 2=both', default=0)
    parser.add_argument('-p', metavar='POWER ITERATION', type=bool, help='power iteration', default=True)
    parser.add_argument('-a', metavar='ONE SHOT METHODS', type=bool, help='one shot methods', default=True)
    parser.add_argument('-n', metavar='INIT', type=int, help='0=random, 1=approximate, 2=both', default=0)
    parser.add_argument('-f', metavar='FILENAME', type=str, help='filename', default='data.tsv')


    args = parser.parse_args()
    basedir = args.d

    output_folder = op.join(basedir, args.o, 'config_files')
    os.makedirs(output_folder, exist_ok=True)

    if args.q == 0:
        qr = ['no_qr']
    elif args.q == 1:
        qr = ['federated_qr']
    else:
        qr = ['no_qr','federated_qr']

    if args.s == 0:
        smpc = [False]
    elif args.s == 1:
        smpc = [True]
    else:
        smpc = [True, False]

    if args.n == 0:
        init = ['random']
    elif args.n == 1:
        init = ['approximate_pca']
    else:
        init = ['random','approximate_pca']

    count = 0
    if args.p:
        count = create_configs_power(output_folder, batch=args.b, train_test=args.t, maxit=args.i, qr=qr, use_smpc=smpc, init=init,
                                     datafile=args.f)
    if args.a:
        create_configs_single_round(output_folder, count, batch=args.b, train_test= args.t, maxit=args.i,use_smpc=smpc,datafile=args.f)




