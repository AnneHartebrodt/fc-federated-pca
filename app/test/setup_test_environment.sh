#clidir=/home/anne/Documents/featurecloud/test-environment/cli
#pydir=/home/anne/Documents/featurecloud/apps/fc-federated-pca/app/test
#basedir=/home/anne/Documents/featurecloud/test-environment/controller/data

basedir=$1
clidir=$2
pydir=$3
echo $pydir
echo $basedir
echo $clidir

outputfolder=$basedir/app_test
mkdir -p $outputfolder

features=10
samples=5000
seed=11
batchcount=3
k=10

# generate the data
python $pydir/generate_test_data.py -d $outputfolder -f data.tsv -n $samples -m $features -s $seed -b $batchcount --means 3,6,1,13,2,3,1,4,89,2 --stds 5,4,3,2,1,1,1,1,1,1

datafile=data.tsv
#datafile=/home/anne/Documents/featurecloud/pca/vertical-pca/data/mnist/scaled/mnnist.tsv
#compute canonical solution
python $pydir/compute_canonical_solution.py -d $outputfolder -f $datafile -k $k -s $seed -b True --header 0 --transpose True

#split the data into batches
sites=4
batch=True
cross_val=True
dirname=batch_cross

python $pydir/generate_splits.py -d $outputfolder -o $dirname -f $datafile -n $sites -s $seed -b $batch -t $cross_val --header 0 --transpose True
python $pydir/generate_config_files.py -d $outputfolder -o $dirname -b $batchcount -t $cross_val

batch=True
cross_val=False
dirname=batch

python $pydir/generate_splits.py -d $outputfolder -o $dirname -f $datafile -n $sites -s $seed -b $batch --header=0 --transpose True
python $pydir/generate_config_files.py -d $outputfolder -o $dirname -b $batch


batch=False
cross_val=False
dirname=single

python $pydir/generate_splits.py -d $outputfolder -o $dirname -f $datafile -n $sites -s $seed --header=0 --transpose True
python $pydir/generate_config_files.py -d $outputfolder -o $dirname