#clidir=/home/anne/Documents/featurecloud/test-environment/cli
#pydir=/home/anne/Documents/featurecloud/apps/fc-federated-pca/app/test
#basedir=/home/anne/Documents/featurecloud/test-environment/controller/data
#datafile=data.tsv
#outputfolder=$basedir/app_test

basedir=$1
clidir=$2
pydir=$3
datafile=$4
outputfolder=$5
seed=$6
sites=$7

echo $pydir
echo $basedir
echo $clidir
mkdir -p $outputfolder

k=10

#compute canonical solution
python $pydir/compute_canonical_solution.py -d $outputfolder -f $datafile -k $k -s $seed -b True --transpose True

#split the data into batches
batch=False
cross_val=False
dirname=single

python $pydir/generate_splits.py -d $outputfolder -o $dirname -f $datafile -n $sites -s $seed --transpose True
python $pydir/generate_config_files.py -d $outputfolder -o $dirname -i 1000 -q 0 -s 0 -a True -p True -n 0