#!/bin/bash

###################################################
#  (S)hell (H)istory (W)riter                     #
#                                                 #
#  Is hooked into zsh/bash shell using special    #
#  'preexec' function.                            #
###################################################

if [[ -z "${SHV_SHELL_HISTORY_ROOT}" ]]; then
    printf 1>&2 "shw.sh: In order to run shw.sh, the SHV_SHELL_HISTORY_ROOT environment variable must first be set.\n"
    exit 1
fi

HOSTNAME="$(hostname)"
LOGFILE="${SHV_SHELL_HISTORY_ROOT}/${HOSTNAME}/$(date +%Y/%m).log"
LOGDIR="$(dirname "$LOGFILE")"
[ -d "$LOGDIR" ] || mkdir -p "$LOGDIR"

if [[ -z "$1" ]]; then
    echo "usage $(basename "$0") COMMAND"
    exit 2
fi

if [[ "$(uname -a)" == *"Darwin"* ]]; then
    SED="gsed"
else
    SED="sed"
fi

CMD="$(echo "$1" | "${SED}" -E ':a;N;$!ba;s/\r{0,1}\n/\\n/g')"; shift
printf "%s:%s:%s:%s:%s\n" "$HOSTNAME" "$(whoami)" "$(date '+%Y%m%d%H%M%S')" "$(pwd)" "$CMD" >> "$LOGFILE";
