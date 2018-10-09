################################################
#  Global Utility Functions for Shell Scripts  #
################################################

function die() {
    MSG="$1"; shift

    if [[ -n "$1" ]]; then
        EC="$1"
    else
        EC=1
    fi

    >&2 printf "ERROR: $MSG\n" | tee >(logger -t "$(basename "$0")")
    exit "$EC"
}

function emsg() {
    MSG="$1"; shift
    printf ">>> $MSG\n"
}

function notify() {
    MSG="$1"
    notify-send "$(basename "$0")" "$MSG"
}