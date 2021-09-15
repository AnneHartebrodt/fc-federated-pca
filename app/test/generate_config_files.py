import yaml
import os.path as op
import os

def make_default_config_file(qr = 'federated_qr'):
    """
    Default config file generator
    qr: one of 'federated_qr'| 'centralised_qr'
    :return:
    """
    dict = {'fc_pca':
             {'input':
                  {'data': 'mnist-test.tsv'},
              'output':
                  {'projections': 'reduced_data.tsv',
                   'left_eigenvectors': 'left_eigenvectors.tsv',
                   'right_eigenvectors': 'right_eigenvectors.tsv',
                   'eigenvalues': 'eigenvalues.tsv',
                   'scaled_data': 'scaled_data.tsv'},
              'algorithm':
                  {'pcs': 5,
                   'algorithm': 'power_iteration',
                   'data_partitioning': 'vertical',
                   'max_iterations': 200,
                   'qr': 'qr',
                   'epsilon': 1e-9},
              'scaling':
                  {'center': False,
                   'scale_variance': False,
                   'transform': 'log2',
                   'scale_dim': 'columns'},
              'settings':
                  {'delimiter': '\t',
                   'rownames': True,
                   'colnames': False,
                   'federated_dimensions': 'columns'},
              'privacy':
                  {'allow_transmission': False,
                   'encryption': 'no_encryption'}
              }
            }
    return dict

def write_config(config, basedir, n):
    for i in range(n):
        os.makedirs(op.join(basedir, str(i)), exist_ok=True)
        with open(op.join(basedir, str(i), 'config.yaml'), 'w') as handle:
            yaml.safe_dump(config, handle, default_flow_style=False, allow_unicode=True)

if __name__ == '__main__':
    basedir = '/home/anne/Documents/featurecloud/apps/fc-federated-pca/app/test/test_data/'
    config = make_default_config_file(qr = 'federated_qr')
    write_config(config=config, basedir=basedir, n=3)