# MNIST

### Set up test environment
```
test_out=mnist
bash fc-federated-pca/app/test/specific_tests/setup_test_environment_mnist.sh $(pwd)/controller/data $(pwd)/cli $(pwd)/fc-federated-pca/app/test $(pwd)/test-data/mnist/mnnist.tsv $test_out

```
### Run the app
```
bash fc-federated-pca/app/test/test.sh $(pwd)/controller/data/ $(pwd)/cli $(pwd)/fc-federated-pca/app/test $test_out
```

### Generate the report
```
mkdir test-output
bash fc-federated-pca/app/test/generate_report.sh $(pwd)/controller/data/ $(pwd)/cli $(pwd)/fc-federated-pca/app/test $test_out  $(pwd)/test-output 
```
