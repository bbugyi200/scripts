#!/bin/bash

###################################################################################################
#  Used to Ensure that a Helper Script is Not Called Directly.                                    #
#                                                                                                 #
# Expects the primary script to create a random hash  and more("secret") and write it to a file   #
# ("secret_file"). Both the hash and the file must then be sent to the helper script as           #
# command-line arguments.                                                                         #
###################################################################################################

secret_file="$1"; shift
secret="$1"; shift
if [[ ! -f "${secret_file}" ]] || [[ "${secret}" != "$(cat "${secret_file}")" ]]; then
    echo "ERROR: $(basename "$0") is not meant to be run directly. Use the emanage script!"
    exit 1
fi
