tmux send-keys -t xmonad "vim ~/.xmonad/xmonad.hs ~/.xmobarrc /usr/share/xmonad/man/xmonad.hs" "Enter"
tmux split-window -t xmonad -h -c '#{pane_current_path}'
tmux split-window -t xmonad -v -c '#{pane_current_path}'
tmux send-keys -t xmonad:0.2 "ghci" "Enter" ":! clear" "Enter"
tmux select-pane -t xmonad:0.0
