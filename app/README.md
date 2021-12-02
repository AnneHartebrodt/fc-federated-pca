# Test pipeline for federated PCA

## Federated PCA
Federated Principal Component Analysis is a versatile .... 

## This document
This document describes a test pipeline to test and validate the federated PCA application for the FeatureCloud platform. The testing involves multiple steps, you may not need to execute all of them depending on your needs. 

1. Data generation and unified preprocessing.
2. Data splitting > Simulation of the federated data sets
3. Simulated federated test runs using the featurecloud testbed via the CLI.
4. Comparison of the results with the baseline.
5. Generation of a test report.

## Data generation and preprocessing
For testing purposes, the data is generated and preprocessed on a single machine. In a federated run, the preprocessing naturally needs to be feasible using federated learning, and appropriate apps are available. Here, we use generated data to test the pipeline. We use small data sets to avoid overly long computation and relatively few variables.


## Directory structures for testing
In order to test the app you can use the script in (Test)[test] to generate artifical data into the following file structure and use the commands in the readme to run the app and generate output files.


### single mode
```
├── baseline_result
│   ├── 11
│   │   ├── eigen.left
│   │   ├── eigen.right
│   │   └── eigen.values
│   ├── 12
│   │   ├── eigen.left
│   │   ├── eigen.right
│   │   └── eigen.values
│   ├── 13
│   │   ├── eigen.left
│   │   ├── eigen.right
│   │   └── eigen.values
│   ├── eigen.left
│   ├── eigen.right
│   └── eigen.values
├── batch
│   ├── config_files
│   │   ├── 0
│   │   │   └── config.yaml
│   │   ├── 1
│   │   │   └── config.yaml
│   │   ├── 2
│   │   │   └── config.yaml
│   │   └── 3
│   │       └── config.yaml
│   └── data_split
│       ├── 0
│       │   ├── 11
│       │   │   └── data.tsv
│       │   ├── 12
│       │   │   └── data.tsv
│       │   └── 13
│       │       └── data.tsv
│       ├── 1
│       │   ├── 11
│       │   │   └── data.tsv
│       │   ├── 12
│       │   │   └── data.tsv
│       │   └── 13
│       │       └── data.tsv
│       ├── 2
│       │   ├── 11
│       │   │   └── data.tsv
│       │   ├── 12
│       │   │   └── data.tsv
│       │   └── 13
│       │       └── data.tsv
│       └── 3
│           ├── 11
│           │   └── data.tsv
│           ├── 12
│           │   └── data.tsv
│           └── 13
│               └── data.tsv
├── batch_cross
│   ├── config_files
│   │   ├── 0
│   │   │   └── config.yaml
│   │   ├── 1
│   │   │   └── config.yaml
│   │   ├── 2
│   │   │   └── config.yaml
│   │   └── 3
│   │       └── config.yaml
│   └── data_split
│       ├── 0
│       │   ├── 11
│       │   │   ├── test
│       │   │   │   └── data.tsv
│       │   │   └── train
│       │   │       └── data.tsv
│       │   ├── 12
│       │   │   ├── test
│       │   │   │   └── data.tsv
│       │   │   └── train
│       │   │       └── data.tsv
│       │   └── 13
│       │       ├── test
│       │       │   └── data.tsv
│       │       └── train
│       │           └── data.tsv
│       ├── 1
│       │   ├── 11
│       │   │   ├── test
│       │   │   │   └── data.tsv
│       │   │   └── train
│       │   │       └── data.tsv
│       │   ├── 12
│       │   │   ├── test
│       │   │   │   └── data.tsv
│       │   │   └── train
│       │   │       └── data.tsv
│       │   └── 13
│       │       ├── test
│       │       │   └── data.tsv
│       │       └── train
│       │           └── data.tsv
│       ├── 2
│       │   ├── 11
│       │   │   ├── test
│       │   │   │   └── data.tsv
│       │   │   └── train
│       │   │       └── data.tsv
│       │   ├── 12
│       │   │   ├── test
│       │   │   │   └── data.tsv
│       │   │   └── train
│       │   │       └── data.tsv
│       │   └── 13
│       │       ├── test
│       │       │   └── data.tsv
│       │       └── train
│       │           └── data.tsv
│       └── 3
│           ├── 11
│           │   ├── test
│           │   │   └── data.tsv
│           │   └── train
│           │       └── data.tsv
│           ├── 12
│           │   ├── test
│           │   │   └── data.tsv
│           │   └── train
│           │       └── data.tsv
│           └── 13
│               ├── test
│               │   └── data.tsv
│               └── train
│                   └── data.tsv
├── data
│   ├── 11
│   │   └── data.tsv
│   ├── 12
│   │   └── data.tsv
│   └── 13
│       └── data.tsv
└── single
    ├── config_files
    │   ├── 0
    │   │   └── config.yaml
    │   ├── 1
    │   │   └── config.yaml
    │   ├── 2
    │   │   └── config.yaml
    │   └── 3
    │       └── config.yaml
    └── data_split
        ├── 0
        │   └── data.tsv
        ├── 1
        │   └── data.tsv
        ├── 2
        │   └── data.tsv
        └── 3
            └── data.tsv


```
