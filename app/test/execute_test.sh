mydir=$(pwd)
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
  # collect all directories in a string separated variable
  cd $controller_data_base_dir
  echo $(pwd)
  dirs=($(ls -d test_data/testing_pca/data_split/*))
  dirs=$(printf "%s," "${dirs[@]}")
  # remove trailing comma
  dirs=$(echo $dirs | sed 's/,*$//g')
  cd $mydir

  #echo $dirs
  python /home/anne/Documents/featurecloud/test-environment/cli/cli.py start --controller-host http://localhost:8000 --client-dirs $dirs --app-image federated_pca_batch:latest --channel local --query-interval 1
  echo "test done"

  # evaluate tests
  # unzip data
  # check
done
# evaluate results