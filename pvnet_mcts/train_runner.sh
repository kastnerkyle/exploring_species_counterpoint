while true
do 
    #python -u train_net_mcts.py 2>&1 | rotatelogs -n 2 trainlog.log 1M
    python -u train_net_mcts.py 2>&1 > trainlog.log
    sleep 1
done
