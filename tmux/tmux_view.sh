#!/bin/bash

###################################################################
#  Utility functions for scripts that initialize "tmux views"     #
# (a particular tmux window layout).                              #
###################################################################

function shell() {
	tmux send-keys "$1" Enter
}

function loop() {
	shell "while true; do $*; done"
}

function split() {
	tmux splitw "$@"
}

function focus() {
	tmux select-pane -t "$1"
}
