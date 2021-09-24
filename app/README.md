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

Using the following command you can generate gaussian data and save them into your base directory ```testing_pca```. The data is generated using a fixed seed, to allow reproducible testing. 

### Single mode
``` 
mydir=./testing_pca
mkdir $mydir
## by default the script generates the data into a subdirectory of the base directory called data
python generate_test_data.py -d $mydir -f test_data.tsv -n 5000 -m 5 --means 0,0,0,0,0 --stds 1,1,1,1,1 -s 11
```

### Batch mode
``` 
batchdir=./testing_pca_batch
mkdir $batchdir
## by default the script generates the data into subdirectories of the base directory called data/SPLIT
python generate_test_data.py -d $batchdir -f test_data.tsv -n 5000 -m 5 --means 0,0,0,0,0 --stds 1,1,1,1,1 -s 11 -b 3
```

## Generate a baseline solution to compare against
In federated principal component analysis, the solution should be equal to the centralised solution. Here, we generate the canoncial solution into a folder ```baseline_results```.

### single mode
```
# data has been generated into data
python compute_canoncial_solution.py -d $mydir -f test_data.tsv -k 10 -s 11
```

### batch mode
```
# set the batch flag
python compute_canoncial_solution.py -d $batchdir -f test_data.tsv -k 10 -s 11 -b
```


## Data splitting
In this section we describe the setup required for the application. The data is split into several subdata sets located in their own directory respectively to be used with the FeatureCloud Testbed. 

Our base directory to generate our test data into is called ```testing_pca```. 

The PCA app offers two modi: a single mode, to compute a single PCA on one data set (single mode), and a batch more, which can be used for instance for feature reduction in a cross validation run (batch mode_. The following illustration show the required directory structure for testing depending on the mode. 


```
python generate_splits.py -d testing_pca/ -f test_data.tsv -n 4 -s 11 
```
```
python generate_splits.py -d $batchdir -f test_data.tsv -n 4 -s 11 -b True
```

## Generate Config files

### single mode
In single mode every partial data set is in its own directory with the associated config file. The config file is used to set up the required parameters. See more on the config file in [insert link here]. The coordinator config file overrules the local configurations, however every local configuration file contains all the information for ease of use.

### batch mode
Note that the batch mode requires the config.yml to be at the same level as the cross-validation splits. The reason for this is, that for cross validation we do not expect different PCA settings to be used for cross validation. Future versions may allow for separate configuration files.



## Directory structures for testing
Your directory strucutre should now look like the following:

### single mode
```
testing_pca
├── baseline_results
│   └── eigenvector.tsv
├── data
│   └── test_data_complete.tsv
└── data_splits
    ├── 1
    │   ├── config.yml
    │   └── test_data.tsv
    └── 2
        ├── config.yml
        └── test_data.tsv

```
### batch mode
```
testing_pca
├── baseline_results
│   └── eigenvector.tsv
├── data
│   └── test_data_complete.tsv
└── data_splits
    ├── 1
    │   ├── 1
    │   │   └── test_data.tsv
    │   ├── 2
    │   │   └── test_data.tsv
    │   └── config.yml
    └── 2
        ├── 1
        │   └── test_data.tsv
        ├── 2
        │   └── test_data.tsv
        └── config.yml


```

##
