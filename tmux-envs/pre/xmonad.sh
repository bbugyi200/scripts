tmux send-keys -t xmonad "vim ~/.xmonad/xmonad.hs ~/.xmobarrc" "Enter"
tmux split-window -t xmonad -h -c '#{pane_current_path}'
tmux select-pane -t xmonad:0.0
