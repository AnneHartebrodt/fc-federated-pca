mydir=$(pwd)

basedir=$1
clidir=$2
pydir=$3
#clidir=/home/anne/Documents/featurecloud/test-environment/cli
#pydir=/home/anne/Documents/featurecloud/apps/fc-federated-pca/app/test
#basedir=/home/anne/Documents/featurecloud/test-environment/controller/data
#
#
# current_test_dir_suffix=app_test/batch_cross


controller_data_test_result=$basedir/tests

count=1
outdirs=()
# "app_test/single" "app_test/batch_cross" "app_test/batch"
suffix_list=( "app_test/single" "app_test/batch_cross" "app_test/batch")

for current_test_dir_suffix in "${suffix_list[@]}"
do
current_test_dir=$basedir/$current_test_dir_suffix
# loop over all configuration files
for configf in $(ls $current_test_dir/config_files)
do
  # start run
  # collect all directories in a string separated variable
  cd $basedir
  echo $(pwd)
  dirs=($(ls -d $current_test_dir_suffix/data_split/*))
  dirs=$(printf "%s," "${dirs[@]}")
  # remove trailing comma
  dirs=$(echo $dirs | sed 's/,*$//g')
  cd $mydir

  # generate a random string to use as the output directory
  outputdir=$(head /dev/urandom | tr -dc A-Za-z0-9 | head -c 13 ; echo '')
  outdirs[${#outdirs[@]}]=$outputdir
  sudo mkdir $controller_data_test_result/$outputdir


  #echo $dirs
  echo python /home/anne/Documents/featurecloud/test-environment/cli/cli.py start --controller-host http://localhost:8000 --client-dirs $dirs --app-image federated_pca_batch:latest --channel local --query-interval 0 \
    --download-results $outputdir --generic-dir $current_test_dir_suffix/config_files/$configf
  python /home/anne/Documents/featurecloud/test-environment/cli/cli.py start --controller-host http://localhost:8000 --client-dirs $dirs --app-image federated_pca_batch:latest --channel internet --query-interval 0 \
    --download-results $outputdir --generic-dir $current_test_dir_suffix/config_files/$configf
  echo "test done"
done
done


# make sure the data is downloaded!!!



