#!/usr/bin/bash
########################################################################################
## Script Name	: venv.sh
## Author      	: Schecter Wolf
## Email       	:
## License 		: Copyright (C) 2024 by John Torres
##
## 				  This program is free software: you can redistribute it and/or modify
## 				  it under the terms of the GNU General Public License as published by
## 				  the Free Software Foundation, either version 3 of the License, or
## 				  (at your option) any later version.
##
## 				  This program is distributed in the hope that it will be useful,
## 				  but WITHOUT ANY WARRANTY; without even the implied warranty of
## 				  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## 				  GNU General Public License for more details.
##
## 				  You should have received a copy of the GNU General Public License
## 				  along with this program.  If not, see <http://www.gnu.org/licenses/>.
## Description	: Wrapper for entering venv for this project
########################################################################################

print_usage() {
    cat << EOF >&2
Description: venv wrapper

Usage: source $(basename "$0") [options]

options:
    -i          initialize

    -h 			Show help

EOF
exit 1
}

main() {
    # Global VARS
    local -r _VENV_NAME="BingoBot"
    local _init=0

    POSITIONAL_PARAMS=""
    while (( "$#" )); do
        case "$1" in
            -i)
                _init=1
                shift
                ;;
            --help|-*|--*=) # unsupported flags
                print_usage
                ;;
            *) # preserve positional arguments
                POSITIONAL_PARAMS="$POSITIONAL_PARAMS $1"
                shift
                ;;
        esac
    done
    eval set -- "$POSITIONAL_PARAMS"

    if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
        >&2 echo "Script must be called as: source $0"
        exit 1
    fi

    # Initialize the new python virtual env if it hasnt already
    if [ ! -d "$_VENV_NAME" ]; then
        # Check if virtualenv exists
        if ! command -v "virtualenv" &> /dev/null; then
            sudo pip install --break-system-packages virtualenv
        fi

        echo "Creating python virtual environment"
        virtualenv $_VENV_NAME
        _init=1
    fi

    # Enter into the python virtual env
    source "$_VENV_NAME/bin/activate"

    # Install the project requirements, if needed
    if [ "$_init" -eq 1 ] && [ -f "./requirements" ]; then
        pip install -r ./requirements.txt
    fi

    echo "Enter command to exit: deactivate"
}

main
