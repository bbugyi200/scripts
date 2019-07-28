# shellcheck disable=SC2154

###################################################################################################
#  Bash module for Gentoo maintenance scripts (which are interfaced via the `emanage` script.     #
###################################################################################################

# shellcheck disable=SC2034
secret_wrapper="emanage"
source secret.sh

trap 'rm ${count_path}' EXIT

MY_XDG_DATA="${XDG_DATA}"/emanage/"$(hostname)"/"${SCRIPTNAME}"
count_path="${MY_XDG_DATA}"/count
[ -d "${MY_XDG_DATA}" ] || mkdir "${MY_XDG_DATA}"

slave_count=0
if [[ -n "$1" ]]; then
    master_count="$1"; shift
else
    master_count=0
fi

function econfirm() {
    echo "${slave_count}" &> "${count_path}"
    slave_count=$((slave_count + 1))

    if [[ "$1" == "-p" ]]; then
        shift
        local prompt="$1"; shift
    fi

    cmd="$1"; shift
    if [[ "${master_count}" -lt "${slave_count}" ]]; then
        if [[ -n "$1" ]]; then
            eval "$1"; shift
        fi

        master_count=$((master_count + 1))

        if [[ -n "${prompt}" ]]; then
            confirm -p "${prompt}" "${cmd}"
        else
            confirm "${cmd}"
        fi

        EC="$?"
        if [[ "${EC}" -ne 0 && "${EC}" -ne 3 ]]; then
            trap - EXIT
            exit "${EC}"
        fi

        return "${EC}"
    fi

    return 1
}

clear
