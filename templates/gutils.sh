###############################################
#  Global Utility Functions for Bash Scripts  #
###############################################

function die() {
    MSG="$1"; shift

    if [[ -n "$1" ]]; then
        EC="$1"
    else
        EC=1
    fi

    echo "$MSG" | tee >(logger -t "$(basename "$0")")
    exit "$EC"
}

function emsg() {
    MSG="$1"; shift
    echo ">>> $MSG"
}

function notify() {
    MSG="$1"; shift
    notify-send "$(basename "$0")" "$MSG"
}
