########################################
#  Utility Functions for Bash Scripts  #
########################################

function die() {
    echo "$1" | tee >(logger -t "$(basename "$0")")
    exit "$2"
}
