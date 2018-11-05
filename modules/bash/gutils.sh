################################################
#  Global Utility Functions for Shell Scripts  #
################################################

# ---------- Global Variables ----------
# shellcheck disable=SC2034
scriptname="$(basename "$0")"
usage="usage: ${scriptname}"

# ---------- XDG User Directories ----------
# shellcheck disable=SC2034
if [[ -n "${XDG_RUNTIME_DIR}" ]]; then
    xdg_runtime="${XDG_RUNTIME_DIR}"
else
    xdg_runtime=/tmp
fi

# shellcheck disable=SC2034
if [[ -n "${XDG_CONFIG_HOME}" ]]; then
    xdg_config="${XDG_CONFIG_HOME}"
else
    xdg_config=/home/"${USER}"
fi

# shellcheck disable=SC2034
if [[ -n "${XDG_DATA_HOME}" ]]; then
    xdg_data="${XDG_DATA_HOME}"
else
    xdg_data=/home/"${USER}"/.local/share
fi

my_xdg_runtime="${xdg_runtime}"/"${scriptname}"
my_xdg_config="${xdg_config}"/"${scriptname}"
my_xdg_data="${xdg_data}"/"${scriptname}"

# ---------- Function Definitions ----------
function die() {
    MSG="$1"; shift

    if [[ -n "$1" ]]; then
        EC="$1"
    else
        EC=1
    fi

    if [[ "${EC}" -eq 2 ]]; then
        MSG="Failed to parse command-line options.\n\n${MSG}"
    fi

    emsg "${MSG}"
    exit "$EC"
}

function emsg() {
    MSG="$1"; shift
    FULL_MSG="[ERROR] $MSG\n"
    >&2 printf "${FULL_MSG}"
    logger -t "${scriptname}" "${FULL_MSG}"
}

function dmsg() {
    MSG="$1"; shift

    # shellcheck disable=SC2154
    if [[ "${debug}" = true ]]; then
        printf "[DEBUG] ${MSG}\n"
    fi
}

function imsg() {
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
