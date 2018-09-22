#!/bin/bash

secret="$1"; shift
secret_file=/tmp/emanage.secret
if [[ ! -f "${secret_file}" ]] || [[ "${secret}" != "$(cat "${secret_file}")" ]]; then
    echo "ERROR: $(basename "$0") is not meant to be run directly. Use the emanage script!"
    exit 1
fi
