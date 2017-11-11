tmux send-keys -t backup "external_backup"
tmux split-window -t backup -h -c '/media/bryan/perseus'
tmux send-keys -t backup:0.1 "sudo mount /dev/sdc /media/bryan/perseus" "Enter"
