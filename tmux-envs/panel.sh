SUBDIR="A"
[[ -n "$1" ]] && SUBDIR=$1

tmux send-keys -t panel:0 "/home/bryan/Dropbox/scripts/C/panel/$SUBDIR" Enter
tmux send-keys -t panel:0 "clear" Enter
tmux command-prompt -I "attach -c \"/home/bryan/Dropbox/scripts/C/panel/$SUBDIR\""
