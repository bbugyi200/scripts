#!/usr/bin/bash

###############################################################################
#  Shared backup functions used by cron backup scripts.                       #
###############################################################################

set -e

export DEFAULT_R=4

BACKUP_DIR=/mnt/hercules/backup
MAX_R=10
RM=/bin/rm

# The maximum amount of time (in milliseconds) for a set of operations to take
# for me to consider it "atomic".
MAX_ATOMIC_TIME=2000

EC=0
TOO_SOON_ERROR=1
NO_ERROR=2
NOT_ATOMIC_ERROR=4
NO_ETBB_ERROR=8
RSYNC_ERROR=16

ERR_MSGS=()

# (E)stimated (T)ime (B)etween (B)ackups
#
# This value should be specified in seconds and should be defined by the client
# script that sourced this library.
ETBB="${ETBB}"

function backup() {
    local from="$1"
    shift

    local to="$1"
    shift

    local R="$1"
    shift

    if [[ "${from}" != *"/" ]]; then
        from="${from}"/
    fi

    if [[ "${to}" != "/"* ]]; then
        to="${BACKUP_DIR}"/"${to}"
    fi
    [[ -d "${to}" ]] || mkdir -p "${to}"

    if [[ -z "${ETBB}" ]]; then
        EC=$((EC | NO_ETBB_ERROR))
        ERR_MSGS+=("The ETBB environment variable was NOT defined while running a $(basename "${to}") backup of ${from%/*}.")

        ETBB=$((60 * 60 * 24 * 365 * 10)) # seconds in 10 years
    fi

    if [[ -f "${to}"/backup.txt ]]; then
        local now="$(date +%s)"
        local last_backup="$(cat "${to}"/backup.txt)"
        local diff=$((now - last_backup))

        # If it has been less than 3/4 the expected time since the last backup
        # was run, something is wrong here. To keep moving forward now would be
        # to risk overwriting older backup rotations.
        local min_tbb=$((ETBB - ETBB / 4))
        if [[ "${diff}" -lt "${min_tbb}" ]]; then
            EC=$((EC | TOO_SOON_ERROR))
            ERR_MSGS+=("It has only been ${diff}s since the last time a $(basename "${to}") backup was run for ${from%/*}.")
            return 0
        fi
    fi

    _backup "${from}" "${to}" "${R}" "${@}"

    if [[ "${BACKUP_ERROR}" -eq 0 ]]; then
        BACKUP_ERROR="${NO_ERROR}"
    fi

    EC=$((EC | BACKUP_ERROR))
}

function backup_home() {
    backup /home home/"$1" "$2" --exclude ".cache" --exclude "bryan/projects/work"
}

function _backup() {
    BACKUP_ERROR=0

    local from="$1"
    shift

    local to="$1"
    shift

    local R="$1"
    shift

    if [[ "${R}" -lt 1 ]]; then
        # No backup should be performed. This allows calls to the backup()
        # function to be effectively "stubbed out" by passing in 0 for the ${R}
        # argument.
        return 0
    elif [[ "${R}" -gt "${MAX_R}" ]]; then
        return 1
    fi

    # We create all of the necessary backup rotation directories now (if they
    # did not already exist). This way we can assume that all of these
    # directories exist going foward and don't have to worry about any annoying
    # errors from `cp`, `mv`, or `rm`.
    [[ -d "${to}" ]] || mkdir -p "${to}"
    local r=2
    while [[ "${r}" -le "${R}" ]]; do
        D="${to}"-"${r}"
        [[ -d "${D}" ]] || mkdir -p "${D}"
        r=$((r + 1))
    done

    # Remove any backups that have been rotated more than R times.
    r=$((R + 1))
    while [[ "${r}" -le "${MAX_R}" ]]; do
        D="${to}"-"${r}"
        [[ -d "${D}" ]] && "${RM}" -rf "${D}" # SLOW
        r=$((r + 1))
    done

    local _to="$(dirname "${to}")"/."$(basename "${to}")"

    # The following line is crucial. Without it, we risk making the first `mv`
    # command in the atomic block (see below) much slower than desired. This
    # will occur if, for example, the machine reboots while the
    # `rm -rf ${to}-${R}` command is being run (see the bottom of this
    # function).
    find "$(dirname "${_to}")" -maxdepth 1 -type d -name "$(basename "${_to}")*" -exec "${RM}" -rf {} \; # SLOW

    # All files/directories added to this array will be deleted at the end of
    # this function.
    local DELETE_LATER=()

    # The main backup is now performed by rsync. Note that the system MAY
    # reboot while this command is running. This is not desirable, but should
    # not be catastrophic either (i.e. it should not corrupt this backup).
    f_rsync_stderr="$(mktemp /tmp/rsync-XXX.err)"
    if rsync -av --delete --delete-excluded "${@}" "${from}" "${_to}" >/dev/null 2>"${f_rsync_stderr}"; then # SLOW
        DELETE_LATER+=("${f_rsync_stderr}")
        date +%s >"${_to}"/backup.txt
    else
        BACKUP_ERROR=$((BACKUP_ERROR | RSYNC_ERROR))
        ERR_MSGS+=("While running a $(basename "${to}") backup of ${from%/*}, rsync failed with the following error(s):\n$(cat "${f_rsync_stderr}")")

        "${RM}" -rf "${_to}"
        "${RM}" -rf "${f_rsync_stderr}"

        return 0
    fi

    # ----- START of Atomic Block
    #
    # The goal is that either (1) ALL of the commands in the following block
    # run or (2) NONE of the commands in the following block run.
    #
    # Everything in this block should be as fast as possible so we minimize
    # the chance of an unexpected reboot corrupting this backup.
    start_atomic_time="$(_time)"
    if [[ "${R}" -eq 1 ]]; then
        local tmp_dir="${_to}".tmp
        DELETE_LATER+=("${tmp_dir}")

        mv "${to}" "${tmp_dir}"
        mv "${_to}" "${to}"
    elif [[ "${R}" -gt 1 ]]; then
        local tmp_dir="${_to}"-"${R}"
        DELETE_LATER+=("${tmp_dir}")

        mv "${to}"-"${R}" "${tmp_dir}"

        r="${R}"
        while [[ "${r}" -gt 2 ]]; do
            mv "${to}"-$((r - 1)) "${to}"-"${r}"
            r=$((r - 1))
        done

        mv "${to}" "${to}"-2
        mv "${_to}" "${to}"
    else
        # This should never happen, right?
        return 3
    fi
    end_atomic_time="$(_time)"
    # ----- END of Atomic Block

    time_spent_in_atomic_block=$((end_atomic_time - start_atomic_time))
    if [[ "${time_spent_in_atomic_block}" -gt "${MAX_ATOMIC_TIME}" ]]; then
        BACKUP_ERROR=$((BACKUP_ERROR | NOT_ATOMIC_ERROR))
        ERR_MSGS+=("While running a $(basename "${to}") backup of ${from%/*}, we took ${time_spent_in_atomic_block}ms to run all commands in an atomic block. This is NOT atomic!")
    fi

    for f in "${DELETE_LATER[@]}"; do
        "${RM}" -rf "${f}" # SLOW
    done
}

function _time() {
    echo $(($(date +%s%N) / 1000000))
}

function post_backup_hook() {
    header="----- ERRORS -----"
    bar="------------------"

    first_error=true
    for err_msg in "${ERR_MSGS[@]}"; do
        if [[ "${first_error}" = true ]]; then
            first_error=false
            printf 1>&2 "%s\n%s\n%s\n" "${bar}" "${header}" "${bar}"
        fi

        printf 1>&2 "* %s\n" "${err_msg}"
    done

    if [[ "${EC}" -eq "${NO_ERROR}" ]]; then
        EC=0
    fi

    return "${EC}"
}
