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

    banner="[ERROR]"
    if [[ "${MSG}" == "usage:"* ]]; then
        banner="${banner}  "
    fi

    >&2 printf "${banner} $MSG\n" | tee >(logger -t "$(basename "$0")")
    exit "$EC"
}

function emsg() {
    MSG="$1"; shift
    printf ">>> $MSG\n"
}

function notify() {
    notify-send "$(basename "$0")" "$@"
}

function truncate() {
    rm "${1}" &> /dev/null
    touch "${1}"
}
