import yaml
import os.path as op
import os
import argparse as ap


def make_default_config_file(algorithm = 'power_iteration',
                             qr='no_qr',
                             init = 'approximate_pca',
                             batch=False):

    """
    Default config file generator
    qr: one of 'federated_qr'| 'no_qr'
    :return:
    """
    dict = {'fc_pca':
             {'input':
                  {'data': 'test_data.tsv',
                   'batch': batch},
              'output':
                  {'projections': 'reduced_data.tsv',
                   'left_eigenvectors': 'left_eigenvectors.tsv',
                   'right_eigenvectors': 'right_eigenvectors.tsv',
                   'eigenvalues': 'eigenvalues.tsv'},
              'algorithm':
                  {'pcs': 10,
                   'algorithm': algorithm,
                   'max_iterations': 500,
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
                   'encryption': 'no_encryption'}
              }
            }
    return dict

def write_config(config, basedir, counter):
    with open(op.join(basedir,  str(counter)+'config.yaml'), 'w') as handle:
        yaml.safe_dump(config, handle, default_flow_style=False, allow_unicode=True)


def create_configs_power(output_folder, batch=False):
    qr = ['federated_qr', 'no_qr']
    init = ['approximate_pca', 'random']

    counter = 0
    for q in qr:
        for i in init:
            config = make_default_config_file(batch=batch,
                                              algorithm='power_iteration',
                                              qr=q,
                                              init=i)
            write_config(config=config, basedir=output_folder, counter=counter)
            counter = counter + 1

def create_configs_approx(output_folder, batch=True):
    config = make_default_config_file(batch=batch, algorithm='approximate_pca')
    write_config(config=config, basedir=output_folder, counter='')


if __name__ == '__main__':
    parser = ap.ArgumentParser(description='Split complete data into test data for federated PCA')
    parser.add_argument('-d', metavar='DIRECTORY', type=str, help='output directory', default='.')
    parser.add_argument('-b', metavar='BATCH', type=bool, help='batch mode', default=False)
    args = parser.parse_args()
    basedir = args.d

    output_folder = op.join(basedir, 'config_files')
    os.makedirs(output_folder, exist_ok=True)
    create_configs_approx(output_folder, batch=args.b)
    create_configs_power(output_folder, batch=args.b)



