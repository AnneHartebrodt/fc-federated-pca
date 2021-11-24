## MNIST

### Set up test environment
```
seed=11
sites=4
test_out=mnist/$seed/$sites
bash fc-federated-pca/app/test/specific_tests/setup_test_environment_mnist.sh $(pwd)/controller/data $(pwd)/cli $(pwd)/fc-federated-pca/app/test $(pwd)/test-data/mnist/mnnist.tsv $test_out $seed $sites
```
### Run tests
```
bash fc-federated-pca/app/test/test.sh $(pwd)/controller/data/ $(pwd)/cli $(pwd)/fc-federated-pca/app/test $test_out
```

### Generate the report
```
mkdir -p test-output/$seed/$sites
bash fc-federated-pca/app/test/generate_report.sh $(pwd)/controller/data/ $(pwd)/cli $(pwd)/fc-federated-pca/app/test $test_out  $(pwd)/test-output/$seed/$sites
```
