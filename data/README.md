# MAYA Training Datasets
wget "https://cse-cic-ids2018.s3.ca-central-1.amazonaws.com/Processed%20Traffic%20Data%20for%20ML%20Algorithms/Friday-02-03-2018_TrafficForML_CICFlowMeter.csv" -O cicids2018.csv
    wget "https://raw.githubusercontent.com/defcom17/NSL_KDD/master/KDDTrain+.txt" -O nslkdd_train.txt
    wget "https://raw.githubusercontent.com/defcom17/NSL_KDD/master/KDDTest+.txt" -O nslkdd_test.txt
python3 detection/train_real.py
