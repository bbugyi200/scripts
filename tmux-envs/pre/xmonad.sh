tmux send-keys -t xmonad "vim ~/.xmonad/xmonad.hs ~/.xmobarrc"
tmux split-window -t xmonad -h
tmux select-pane -t xmonad:0.0
