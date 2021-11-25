## MNIST

### Set up test environment
```
test_out=tcga/
bash fc-federated-pca/app/test/specific_tests/setup_test_environment_mnist.sh $(pwd)/controller/data $(pwd)/cli $(pwd)/fc-federated-pca/app/test $(pwd)/test-data/mnist/mnnist.tsv $test_out $seed $sites
```
### Run tests
```
bash fc-federated-pca/app/test/test.sh $(pwd)/controller/data/ $(pwd)/cli $(pwd)/fc-federated-pca/app/test $test_out
```

### Generate the report
```
mkdir -p mnist-output/$seed/$sites
bash fc-federated-pca/app/test/generate_report.sh $(pwd)/controller/data/ $(pwd)/cli $(pwd)/fc-federated-pca/app/test $test_out  $(pwd)/test-output/$seed/$sites
```
### Batchify
```
for seed in {11..20};
do
for sites in 3 5 10;
test_out=mnist/$seed/$sites
mkdir -p $test_out
# generate data
bash fc-federated-pca/app/test/specific_tests/setup_test_environment_mnist.sh $(pwd)/controller/data $(pwd)/cli $(pwd)/fc-federated-pca/app/test $(pwd)/test-data/mnist/mnnist.tsv $test_out $seed $sites
# run test
bash fc-federated-pca/app/test/test.sh $(pwd)/controller/data/ $(pwd)/cli $(pwd)/fc-federated-pca/app/test $test_out
done
done
```
```
for seed in {11..20};
do
for sites in 3 5 10;
mkdir -p mnist-output/$seed/$sites
# generate report
bash fc-federated-pca/app/test/generate_report.sh $(pwd)/controller/data/ $(pwd)/cli $(pwd)/fc-federated-pca/app/test $test_out  $(pwd)/test-output/$seed/$sites
done
done
```
