#!/bin/bash

###################################################################################################
#  Used to Ensure that a Helper Script is Not Called Directly.                                    #
#                                                                                                 #
# Expects the primary script to create a random hash  and more("secret") and write it to a file   #
# ("secret_file"). Both the hash and the file must then be sent to the helper script as           #
# command-line arguments.                                                                         #
#                                                                                                 #
# The ${secret_wrapper} variable must be set before sourcing secret.sh into the client.    #
###################################################################################################

source /home/bryan/Dropbox/scripts/modules/bash/gutils.sh

# shellcheck disable=SC2154
if [[ -z "${secret_wrapper}" ]]; then
    echo "The \${secret_wrapper} variable is NOT defined."
    exit 1
fi

secret="$1"; shift
secret_file="/tmp/${secret_wrapper}.secret"
if [[ ! -f "${secret_file}" ]] || [[ "${secret}" != "$(cat "${secret_file}")" ]]; then
    die "$(basename "$0") is not meant to be run directly. Use the ${secret_wrapper} script!"
fi
