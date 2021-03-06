#!/usr/bin/bash

###############################################################################
#  Shared utility functions used by cron 'jobs' scripts.                      #
###############################################################################

# ensure running as bryan
if [ "$(id -u)" != "$(id -u bryan)" ]; then
    exec sudo -u bryan "$0" "$@"
fi

if [[ "$1" == "-v" || "$1" == "--verbose" ]]; then
    shift
    VERBOSE=true
fi

source "${HOME}"/.profile

DELETE_LATER=()
EC=0
LAST_EC=0

# Should be defined by the main script that sources job.sh.
SCRIPTNAME="${SCRIPTNAME}"

trap "_exit_handler" INT TERM EXIT
set -e

function _exit_handler() {
    for f in "${DELETE_LATER[@]}"; do
        rm -rf "${f}"
    done
}

FIRST_UNSAFE_CMD=true
function unsafe_cmd() {
    local cmd="$1"
    shift

    local cmd_stdout_f="$(mktemp "/tmp/daily_jobs-${cmd%% *}-XXX.out")"
    DELETE_LATER+=("${cmd_stdout_f}")

    local logfile=/var/tmp/"${SCRIPTNAME}".log

    if [[ "${FIRST_UNSAFE_CMD}" = true ]]; then
        FIRST_UNSAFE_CMD=false

        printf "TIMESTAMP: " > "${logfile}"
        date +"%Y-%m-%d %H:%M:%S" >> "${logfile}"
        echo "------------------------------" >> "${logfile}"
    fi

    local out_files=("${logfile}")
    if [[ "${VERBOSE}" = true ]]; then
        out_files+=(/dev/stderr)
    fi

    printf "unsafe_cmd: %s  " "${cmd}" | tee -a "${out_files[@]}" >/dev/null
    eval "${cmd}" >"${cmd_stdout_f}"
    printf "[%s]\n" "$(date +%H:%M:%S)" | tee -a "${out_files[@]}" >/dev/null

    LAST_EC=$?
    if [[ "${LAST_EC}" -ne 0 ]]; then
        EC=$((EC | LAST_EC))

        cat 1>&2 "${cmd_stdout_f}"
        printf 1>&2 "%s: exited with return code %d\n\n" "${cmd}" "${LAST_EC}"
    fi
}
