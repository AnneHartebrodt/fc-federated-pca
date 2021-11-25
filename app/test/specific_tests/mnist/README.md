## TCGA

### Set up test environment
```
seed=11
test_out=app_test_tcga
bash fc-federated-pca/app/test/specific_tests/setup_test_environment_mnist.sh $(pwd)/controller/data $(pwd)/cli $(pwd)/fc-federated-pca/app/test $(pwd)/test-data/cancer_type_site $test_out $seed
```
### Run tests
```
split_dir=split_dir
suffix_list=( "$test_out/single" )
bash fc-federated-pca/app/test/test.sh $(pwd)/controller/data/ $(pwd)/cli $(pwd)/fc-federated-pca/app/test $test_out $split_dir $suffix_list
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
do
test_out=mnist/$seed/$sites
echo $test_out
mkdir -p $test_out
# generate data
bash fc-federated-pca/app/test/specific_tests/mnist/setup_test_environment_mnist.sh $(pwd)/controller/data $(pwd)/cli $(pwd)/fc-federated-pca/app/test $(pwd)/test-data/mnist/mnnist.tsv $test_out $seed $sites
# run test

split_dir=split_dir
suffix_list=( "$test_out/single" )
bash fc-federated-pca/app/test/test.sh $(pwd)/controller/data/ $(pwd)/cli $(pwd)/fc-federated-pca/app/test $test_out $split_dir $suffix_list
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
