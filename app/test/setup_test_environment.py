import app.test.generate_test_data as td
import app.test.generate_config_files as cf
import app.test.generate_splits as gs


import os
import numpy as np
import  scipy as sc
import pandas as pd


if __name__ == '__main__':
    basedir = '/home/anne/Documents/featurecloud/test-environment/test_data'

    splits = 3
    total_samples = 500
    variables = 10

    variable_means = [1,1,1,1,1,1,1,1,1,1]
    variable_stds = [1,1,1,1,1,1,1,1,1,1]

    # make the base directory if not existent
    os.makedirs(basedir, exist_ok=True)

    # generate the data
    data= td.generate_data(number_features=variables,
                           number_samples=total_samples,
                           variable_means=variable_means,
                           variable_stds= variable_stds)

    # generate the canonical solution

