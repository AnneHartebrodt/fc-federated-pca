# Singular Value Decomposition App

## Perform singular values decomposition (SVD) on tabular data
Singular value decomposition is the standard way of performing PCA on large datasets because it avoids computing the covariance matrix. In federated learning, there are exact and approximate SVD, which are both implemented in this application.

## Configuration file:
Use this standard configuration file to set up your workflow. When assembling your workflow, you need to create one config file for the entiere workflow. The format is .yml/.yaml standard.

```
fc_pca:
  algorithm:
    algorithm: approximate_pca ## choose approximate_pca or power_iteration
    epsilon: 1.0e-09 ## convergence criterion for power iteration only
    init: approximate_pca ## initialisation method for power iteration only (random or approximate_pca (recommended))
    max_iterations: 500 ## maximal number of iterations for power iteration
    pcs: 10 ## number of eigenvectors.
    qr: no_qr ## federated_qr or no_qr (recommended)
  input:
    batch: false ## use a batch setting where multiple subdirectories are decomposed simulatenously
    data: test_data.tsv # name of the test data set
  output:
    eigenvalues: eigenvalues.tsv ## standard output file names
    left_eigenvectors: left_eigenvectors.tsv
    projections: reduced_data.tsv
    right_eigenvectors: right_eigenvectors.tsv
  privacy:
    allow_transmission: false 
    encryption: no_encryption
  settings:
    colnames: false ## data table settings
    delimiter: "\t"
    rownames: false

```
