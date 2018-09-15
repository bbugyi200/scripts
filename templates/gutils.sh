###############################################
#  Global Utility Functions for Bash Scripts  #
###############################################

function die() {
    if [[ -z "$1" ]]; then
        echo "usage: die MSG [EXIT_CODE]"
        exit 2
    fi

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
    if [[ -z "$1" ]]; then
        echo "usage: emsg MSG"
        exit 2
    fi

    MSG="$1"; shift
    echo ">>> $MSG"
}
