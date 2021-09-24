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

def write_config(config, basedir, n):
    with open(op.join(basedir,  'config.yaml'), 'w') as handle:
        yaml.safe_dump(config, handle, default_flow_style=False, allow_unicode=True)

if __name__ == '__main__':
    parser = ap.ArgumentParser(description='Split complete data into test data for federated PCA')
    parser.add_argument('-d', metavar='DIRECTORY', type=str, help='output directory', default='.')
    parser.add_argument('-b', metavar='BATCH', type=bool, help='batch mode', default=False)
    args = parser.parse_args()
    basedir = args.d

    # make the output folder
    output_folder = op.join(basedir, 'config_files')
    os.makedirs(output_folder, exist_ok=True)

    config = make_default_config_file()
    write_config(config=config, basedir=output_folder, n=3)

    #algorithm = ['power_iteration']
    #qr = ['federated_qr', 'no_qr']
    #approximate_pca = [True, False]
    #init = ['approximate_pca', 'random']
    #batch = [True, False]
