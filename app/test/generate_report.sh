test_report=/home/anne/Documents/featurecloud/apps/tests

basedir=/home/anne/Documents/featurecloud/test-environment/controller/data
pydir=/home/anne/Documents/featurecloud/apps/fc-federated-pca/app/test

sudo mkdir -p $test_report

seed=11
for od in $(ls $basedir/tests/$od )
do
    # collect all output files in a string separated variable
  cd $basedir/tests/$od
  echo $(pwd)
  # get number of clients
  declare -i clients=$(ls *.zip| wc -l)

  for i in $(seq 0 $(($clients -1)))
  do

    sudo unzip -d client_$i $(ls | grep  client_$i)
  done

  cl=($(ls -l . | egrep '^d' | rev | cut -f1 -d' ' | rev))
  #collect the relevant files

  if [ $(grep -e 'batch: true' $cl/config.yaml -c) = 1 ]
    then
      # batch mode
      # check of train/test
      dirs=($(ls -l $cl | egrep '^d' | rev | cut -f1 -d' ' | rev))
      for d in "${dirs[@]}"
      do
      if [ -d $cl/$d/test ]
      then
        echo 'batch & cross validation'
        tests=$(printf "$basedir/tests/$od/%s/$d/test/right_eigenvectors.tsv " "${cl[@]}")
        trains=$(printf "$basedir/tests/$od/%s/$d/train/right_eigenvectors.tsv " "${cl[@]}");
        python $pydir/check_accuracy.py -d $test_report -r $tests -R $basedir/app_test/baseline_result/$d/eigen.right -l $basedir/tests/$od/$cl/$d/test/left_eigenvectors.tsv \
       -L $basedir/app_test/baseline_result/$d/eigen.left -o $od"_"$d"_test.tsv" -e $basedir/tests/$od/$cl/config.yaml
       python $pydir/check_accuracy.py -d $test_report -r $trains -R $basedir/app_test/baseline_result/$d/eigen.right -l $basedir/tests/$od/$cl/$d/test/left_eigenvectors.tsv \
       -L $basedir/app_test/baseline_result/$d/eigen.left -o $od"_"$d"_train.tsv" -e $basedir/tests/$od/$cl/config.yaml
      else
        echo 'only batch'
        tests=$(printf "$basedir/tests/$od/%s/$d/right_eigenvectors.tsv " "${cl[@]}")
        python $pydir/check_accuracy.py -d $test_report -r $tests -R $basedir/app_test/baseline_result/$d/eigen.right -l $basedir/tests/$od/$cl/$d/left_eigenvectors.tsv \
       -L $basedir/app_test/baseline_result/$d/eigen.left -o $od"_"$d"_test.tsv" -e $basedir/tests/$od/$cl/config.yaml
      fi
      done

    else
      echo 'single mode'
      tests=$(printf "$basedir/tests/$od/%s/right_eigenvectors.tsv " "${cl[@]}")
      echo $tests
      python $pydir/check_accuracy.py -d $test_report -r $tests -R $basedir/app_test/baseline_result/$seed/eigen.right -l $basedir/tests/$od/$cl/left_eigenvectors.tsv \
       -L $basedir/app_test/baseline_result/$seed/eigen.left -o $od"_"$d"_test.tsv" -e $basedir/tests/$od/$cl/config.yaml

    fi
  cd ..
done

# generate report
python $pydir/generate_report.py -d $test_report/test_results -r $test_report/report.md
pandoc $test_report/report.md -f markdown -t html -s -o $test_report/report.html --css $pydir/templates/pandoc.css
