import numpy as np
import scipy as sc
import pandas as pd
import os
import argparse as ap

def generate_data(number_features, number_samples, variable_means=None, variable_stds=None, seed=11):
    """
    Returns generated gaussian data either standard normal, if no means and standard deviations
    are given, or according to the given parameters.
    :param number_features: Number of variables to generate
    :param number_samples: Number of samples to generate
    :param variable_means: Optional vector of means for variables
    :param variable_stds: Optional vector of standard deviations for variables
    :param seed: random seed
    :return: numpy array of generated data containing samples (rows) x features (colums)
    """
    if variable_means is not None:
        assert  len(variable_means) == len(variable_stds), "Number of means and stds should be equal"
        assert len(variable_means) == number_features, "Number of variables should be eqaul to length of mean/std vectors"
    generated_data = []
    for nf in range(number_features):
        if variable_means is None:
            generated_data.append(np.random.standard_normal(number_samples))
        else:
            generated_data.append(np.random.normal(size=number_samples, loc=variable_means[nf], scale=variable_stds[nf]))
    generated_data = np.stack(generated_data, axis=1)
    return generated_data


if __name__ == '__main__':
    parser = ap.ArgumentParser(description='Generate sample data for federated PCA')
    parser.add_argument('-f', metavar='FILE', type=str, help='filename of data file')
    parser.add_argument('-n', metavar='SAMPLES', type=int, help='Number of samples')
    parser.add_argument('-m', metavar='VARIABLES', type=int, help='Number of variables')
    parser.add_argument('--means', metavar='VARIABLE_MEANS', type=str, help='Variable means, if omitted 0', default=None)
    parser.add_argument('--stds', metavar='VARIABLE_STDS', type=str, help='Variable standard deviations, if omitted 1', default=None)
    args = parser.parse_args()
    basedir = '.'

    total_samples = 500
    variables = 10

    if args.means is not None and args.stds is not None:
        variable_means = [int(m) for m in args.means.split(',')]
        variable_stds = [int(m) for m in args.stds.split(',')]
        assert len(variable_means) == len(variable_stds), 'Length of mean and std vector must match'
        assert len(variable_means) == args.m, 'Length of mean and variable vector need to match number of variables'
        # make the base directory if not existent
    else:
        print('Falling back to standard normal')
        variable_means = None
        variable_stds = None


    data = generate_data(number_features=args.m, number_samples=args.n, variable_means=variable_means, variable_stds=variable_stds)
    pd.DataFrame(data).to_csv(args.f, sep='\t', header=False, index=False)