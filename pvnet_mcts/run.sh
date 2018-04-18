bash gen_runner.sh &
bash train_runner.sh &

while true
do
    echo "run.sh bash subprocesses status:"
    echo $(ps aux | grep $USER | grep runner.sh)
    sleep 30
done
