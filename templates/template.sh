#!/bin/bash



source /home/bryan/Dropbox/scripts/templates/gutils.sh

# ---------- Command-line Arguments ----------
eval set -- "$(getopt -o "d,h,q" -l "debug,help,quiet" -- "$@")"

USAGE="usage: $(basename "$0") [-d] [-h] [-q]"

read -r -d '' HELP << EOM
$USAGE
EOM

while [[ -n "$1" ]]; do
    case $1 in
       -d|--debug )
           debug=true
           ;;
       -h|--help )
           echo "$HELP"
           exit 0
           ;;
       -q|--quiet )
           quiet=true
           ;;
       -- )
           shift
           break
           ;;
    esac
    shift
done

LOG_FILE=/var/tmp/"$(basename "$0")".log
if [[ "$debug" = true ]] && [[ "$quiet" = true ]]; then
    exec > "$LOG_FILE"
elif [[ "$debug" = true ]]; then
    exec > >(tee "$LOG_FILE")
elif [[ "$quiet" = true ]]; then
    exec > /dev/null
fi

if [[ "$debug" = true ]] || [[ "$quiet" = true ]]; then
    exec 2>&1
fi

if [[ "$debug" = true ]]; then
    PS4='$LINENO: '
    set -x
fi

# ---------- Main ----------
