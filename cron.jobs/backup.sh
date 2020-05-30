#!/usr/bin/env bash

###############################################################################
#  Shared backup functions used by cron backup scripts.                       #
###############################################################################

set -e

BACKUP_DIR=/media/bryan/hercules/backup
KCONF_DIR="${BACKUP_DIR}"/kernel_configs
DEFAULT_R=4
MAX_R=10

# The maximum amount of time (in milliseconds) for a set of operations to take
# for me to consider it "atomic".
MAX_ATOMIC_TIME=2000

EC=0
TOO_SOON_ERROR=1
NO_ERROR=2
NOT_ATOMIC_ERROR=4

ERR_MSGS=()

# (E)stimated (T)ime (B)etween (B)ackups
#
# This value should be specified in seconds and should be defined by the client
# script that sourced this library.
ETBB="${ETBB}"

function backup() {
    local from="$1"; shift
    local to="$1"; shift
    local R="$1"; shift

    if [[ "${from}" != *"/" ]]; then
        from="${from}"/
    fi

    if [[ "${to}" != "/"* ]]; then
        to="${BACKUP_DIR}"/"${to}"
    fi
    [[ -d "${to}" ]] || mkdir -p "${to}"

    if [[ -z "${ETBB}" ]]; then
        ETBB=$((60 * 60 * 24 * 365 * 10))  # seconds in 10 years
    fi

    if [[ -f "${to}"/backup.txt ]]; then
        local now="$(date +%s)"
        local last_backup="$(cat "${to}"/backup.txt)"
        local diff=$((now - last_backup))

        local min_tbb=$((ETBB - ETBB / 4))

        # If it has been less than 3/4 the expected time since the last backup
        # was run, something is wrong here. To keep moving forward now would be
        # to risk overwriting older backup rotatons.
        if [[ "${diff}" -lt "${min_tbb}" ]]; then
            EC=$((EC | TOO_SOON_ERROR))
            ERR_MSGS+=("It has only been ${diff}s since the last time a $(basename "${to}") backup was run for ${from%/*}.")
            return 0
        fi
    fi

    _backup "${from}" "${to}" "${R}" "${@}"

    EC=$((EC | NO_ERROR))
}

function backup_home() {
    backup /home home/"$1" "$2" --exclude ".cache" --exclude "bryan/Sync/var/projects/edgelp"
}

function _backup() {
    local from="$1"; shift
    local to="$1"; shift
    local R="$1"; shift

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
    local r=2
    while [[ "${r}" -le "${R}" ]]; do
        D="${to}"-"${r}"
        [[ -d "${D}" ]] || mkdir -p "${D}"
        r=$((r + 1))
    done

    # Remove any backups that have been rotated more than R times.
    #
    # This can be slow but that's OK as long as we don't expect the commands
    # included in or above this block to be atomic.
    r=$((R + 1))
    while [[ "${r}" -le "${MAX_R}" ]]; do
        D="${to}"-"${r}"
        [[ -d "${D}" ]] && rm -rf "${D}"  # SLOW
        r=$((r + 1))
    done

    local _to="$(dirname "${to}")"/."$(basename "${to}")"

    # The following line is crucial. Without it, we risk making the first `mv`
    # command in the atomic block (see below) much slower than desired. This
    # will occur if, for example, the machine reboots while the
    # `rm -rf ${to}-${R}` command is being run (see the bottom of this
    # function).
    find "$(dirname "${_to}")" -maxdepth 1 -type d -name "$(basename "${_to}")*" -exec rm -rf {} \;  # SLOW

    # Since `cp` commands are much slower than `mv` commands, we copy this
    # directory here--with the full expectation that the system MAY reboot
    # while this command is running--and then place a corresponding `mv`
    # command in the atomic block below (which should run much faster).
    cp -p -r -f "${to}" "${_to}"  # SLOW

    # The main backup is now performed by rsync. Note that the system MAY
    # reboot while this command is running. This is not desirable, but should
    # not be catastrophic either (i.e. it should not curropt this backup).
    rsync -av --delete --delete-excluded "${@}" "${from}" "${_to}"  # SLOW
    date +%s > "${_to}"/backup.txt

    local DIRS_AND_FILES_TO_RM=()

    # ----- START of Atomic Block
    #
    # The goal is that either (1) ALL of the commands in the following block
    # run or (2) NONE of the commands in the following block run.
    #
    # Everything in this block should be as fast as possible so we minimize
    # the chance of an unexpected reboot corrupting this backup.

    start_atomic_time="$(_time)"
        if [[ "${R}" -eq 1 ]]; then
            mv "${to}" "${tmp_to_dir}"
            mv "${_to}" "${to}"
        elif [[ "${R}" -gt 1 ]]; then
            mv "${to}"-"${R}" "${tmp_to_dir}"
            
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

    atomic_diff=$((end_atomic_time - start_atomic_time))
    if [[ "${atomic_diff}" -gt "${MAX_ATOMIC_TIME}" ]]; then
        EC=$((EC | NOT_ATOMIC_ERROR))
        ERR_MSGS+=("While running a $(basename ${to}) backup of ${from%/*}, we took ${atomic_diff}ms to run all commands in an atomic block. This is NOT atomic!")
    fi

    rm -rf "${tmp_to_dir}"  # SLOW
}

function _time() {
    echo $(($(date +%s%N) / 1000000))
}

function backup_kernel_config() {
    local P="$1"; shift

    [[ -d "${KCONF_DIR}" ]] || mkdir -p "${KCONF_DIR}"

    /bin/cp -f /usr/src/linux/.config "${KCONF_DIR}"/"${P}"-"$(date +%Y%m%d%H%M%S)"-"$(uname -r)".config

    KMAX=5
    if [[ "$(find "${KCONF_DIR}" -type f -name "${P}*" | wc -l)" -gt "${KMAX}" ]]; then
        find "${KCONF_DIR}" -type f -name "${P}*" | sort -u | head -n -"${KMAX}" | xargs /bin/rm
    fi
}

function post_backup_hook() {
    header="----- ERRORS -----"
    bar="------------------"

    first_error=true
    for err_msg in "${ERR_MSGS[@]}"; do
        if [[ "${first_error}" = true ]]; then
            first_error=false
            1>&2 printf "%s\n%s\n%s\n" "${bar}" "${header}" "${bar}"
        fi

        1>&2 printf "* %s\n" "${err_msg}"
    done

    if [[ "${EC}" -eq "${NO_ERROR}" ]]; then
        EC=0
    fi

    return "${EC}"
}
