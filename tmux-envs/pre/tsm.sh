SERVER="east"
[[ -n "$1" ]] && SERVER="$1"

tmux send-keys -t tsm "tsm-start" Enter
tmux send-keys -t tsm "PIA start $SERVER" Enter
tmux split-window -t tsm -h
tmux send-keys -t tsm:0.1 "tsm-watch" Enter
tmux select-pane -t tsm:0.0
