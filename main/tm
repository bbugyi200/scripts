#!/bin/bash

if [ "$1" = 'ls' ]
then 
    tmux ls
elif [ "$#" -eq 0 ]
then
    tmux -2
else
    tmux attach-session -t $1 || tmux new-session -s $1
fi
