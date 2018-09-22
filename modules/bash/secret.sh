#!/bin/bash

secret_file="$1"; shift
secret="$1"; shift
if [[ ! -f "${secret_file}" ]] || [[ "${secret}" != "$(cat "${secret_file}")" ]]; then
    echo "ERROR: $(basename "$0") is not meant to be run directly. Use the emanage script!"
    exit 1
fi
