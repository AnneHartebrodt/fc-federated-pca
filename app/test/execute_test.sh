controller_data_base_dir=/home/anne/Documents/featurecloud/test-environment/controller/data
controller_data_test_dir=/home/anne/Documents/featurecloud/test-environment/controller/data/test_data/testing_pca
clidir=/home/anne/Documents/featurecloud/test-environment/cli
# move config file to correct directory
for configf in $(ls $controller_data_test_dir/config_files)

do
  echo $configf
  for subdirs in $(ls $controller_data_test_dir/data_split)
  do
    # copy the config file into every subfolder and rename
    echo $controller_data_test_dir/data_split/$subdirs/config.yml
    cp $controller_data_test_dir/config_files/$configf $controller_data_test_dir/data_split/$subdirs/config.yml
  done
# start run
  echo $clidir/cli.py
  python /home/anne/Documents/featurecloud/test-environment/cli/cli.py start --controller-host http://localhost:8000 --client-dirs test_data/testing_pca/data_split/0,test_data/testing_pca/data_split/1,test_data/testing_pca/data_split/2 --app-image federated_pca_batch:latest --channel local --query-interval 1
  echo "test done"
done
# evaluate results