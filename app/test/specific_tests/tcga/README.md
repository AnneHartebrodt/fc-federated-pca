## TCGA

### Batchify

```
test_out=tcga
seed=11
echo $test_out
mkdir -p $test_out
# generate data
bash fc-federated-pca/app/test/specific_tests/tcga/setup_test_environment_tcga.sh $(pwd)/controller/data $(pwd)/cli $(pwd)/fc-federated-pca/app/test $(pwd)/test-data/cancer_type_site $test_out $seed 

# run test
split_dir=data
for ct in $(ls $(pwd)/test-data/cancer_type_site)
do
while [ $(docker container ls -q | wc -w) -gt 2 ]
do
echo 'Waiting for containers to finish before spawning new ones'
sleep 1m
done
 
bash fc-federated-pca/app/test/test.sh $(pwd)/controller/data/ $(pwd)/cli $(pwd)/fc-federated-pca/app/test $test_out/$ct $split_dir
sleep 1m
done
done
```


