while true
do
    python -u generate_buffer_data_net_mcts.py 2>&1 | rotatelogs -n 2 genlog.log 1M
    sleep 1
done
