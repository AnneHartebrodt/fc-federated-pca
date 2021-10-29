outputfolder=/home/anne/Documents/featurecloud/test-environment/controller/data/app_test
mkdir -p $outputfolder

features=10
samples=5000
seed=11
batchcount=3
k=10

# generate the data
python generate_test_data.py -d $outputfolder -f data.tsv -n $samples -m $features -s $seed -b $batchcount

#compute canonical solution
python compute_canonical_solution.py -d $outputfolder -f data.tsv -k $k -s $seed -b True --header 0 --transpose True

#split the data into batches
sites=4
batch=True
cross_val=True
dirname=batch_cross

python generate_splits.py -d $outputfolder -o $dirname -f data.tsv -n $sites -s $seed -b $batch -t $cross_val --header 0 --transpose True
python generate_config_files.py -d $outputfolder -o $dirname -b $batchcount -t $cross_val

batch=True
cross_val=False
dirname=batch

python generate_splits.py -d $outputfolder -o $dirname -f data.tsv -n $sites -s $seed -b $batch --header=0 --transpose True
python generate_config_files.py -d $outputfolder -o $dirname -b $batch


batch=False
cross_val=False
dirname=single

python generate_splits.py -d $outputfolder -o $dirname -f data.tsv -n $sites -s $seed --header=0 --transpose True
python generate_config_files.py -d $outputfolder -o $dirname