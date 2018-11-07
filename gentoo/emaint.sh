# shellcheck disable=SC2154

###################################################################################################
#  Bash module for Gentoo maintenance scripts (which are interfaced via the `emanage` script.     #
###################################################################################################

# shellcheck disable=SC2034
secret_wrapper="emanage"
source /usr/lib/secret.sh

trap 'rm ${count_path}' EXIT

my_xdg_data="${xdg_data}"/emanage/"$(hostname)"/"${scriptname}"
count_path="${my_xdg_data}"/count
[ -d "${my_xdg_data}" ] || mkdir "${my_xdg_data}"

slave_count=0
if [[ -n "$1" ]]; then
    master_count="$1"; shift
else
    master_count=0
fi

function econfirm() {
    echo "${slave_count}" &> "${count_path}"
    slave_count=$((slave_count + 1))

    cmd="$1"; shift
    if [[ "${master_count}" -lt "${slave_count}" ]]; then
        if [[ -n "$1" ]]; then
            eval "$1"; shift
        fi

        master_count=$((master_count + 1))
        confirm "${cmd}"
        EC="$?"
        if [[ "${EC}" -ne 0 && "${EC}" -ne 3 ]]; then
            trap - EXIT
            exit 0
        fi

        return "${EC}"
    fi

    return 1
}

clear
