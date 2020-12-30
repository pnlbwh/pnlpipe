#!/usr/bin/env bash

set -o pipefail  # fail if any command in a pipe fails

#declare -r INTERACTIVE_MODE="$([ tty --silent ] && echo on || echo off)"
declare -r INTERACTIVE_MODE="on"

SCRIPT_NAME=$(readlink -m "$0")
SCRIPT_NAME=${SCRIPT_NAME##*/}
if [ -z "${SCRIPTDIR-}" ]; then
    SCRIPTDIR=$(dirname "$0")
fi

#--------------------------------------------------------------------------------------------------
# Begin Help Section

HELP=""
HELP_TEXT=""

usage() {
    retcode=${1:-0}
    if [ -n "$HELP" ]; then
        echo -e "${HELP}";
    elif [ -n "$HELP_TEXT" ]; then
        echo -e "$HELP_TEXT"
    else
        echo ""
    fi
    exit $retcode;
}

# End Help Section
#--------------------------------------------------------------------------------------------------

#--------------------------------------------------------------------------------------------------
# Begin Logging Section
if [[ "${INTERACTIVE_MODE}" == "off" ]]
then
    # Then we don't care about log colors
    declare -r LOG_DEFAULT_COLOR=""
    declare -r LOG_ERROR_COLOR=""
    declare -r LOG_INFO_COLOR=""
    declare -r LOG_SUCCESS_COLOR=""
    declare -r LOG_WARN_COLOR=""
    declare -r LOG_DEBUG_COLOR=""
else
    declare -r LOG_DEFAULT_COLOR="\033[0m"
    declare -r LOG_ERROR_COLOR="\033[1;31m"
    declare -r LOG_INFO_COLOR="\033[1m"
    declare -r LOG_SUCCESS_COLOR="\033[1;32m"
    declare -r LOG_WARN_COLOR="\033[1;33m"
    declare -r LOG_DEBUG_COLOR="\033[1;34m"
fi

# This function scrubs the output of any control characters used in colorized output
# It's designed to be piped through with text that needs scrubbing.  The scrubbed
# text will come out the other side!
prepare_log_for_nonterminal() {
    # Essentially this strips all the control characters for log colors
    sed "s/[[:cntrl:]]\[[0-9;]*m//g"
}

scrubcolors() {
    sed -i "s/[[:cntrl:]]\[[0-9;]*m//g" $1
}

log() {
    local log_text="$1"
    local log_level="${2:-"INFO"}"
    local log_color="${3:-"$LOG_INFO_COLOR"}"

    if [[ $log_level == "INFO" ]]; then
        log_text_color=$LOG_WARN_COLOR
    elif [[ $log_level == "SUCCESS" ]]; then
        log_text_color=$LOG_SUCCESS_COLOR
    else
        log_text_color=$log_color
    fi
    #echo -e "${LOG_INFO_COLOR}[$(date +"%Y-%m-%d %H:%M:%S %Z")] [${log_level}] [$PWD] [$SCRIPTDIR/$SCRIPT_NAME] ${log_text_color} ${log_text} ${LOG_DEFAULT_COLOR}" >&2;
    #echo -e "${LOG_INFO_COLOR}$(date +"%Y-%m-%d %H:%M:%S") | ${log_level} | $PWD | $SCRIPTDIR/$SCRIPT_NAME ${log_text_color} ${log_text} ${LOG_DEFAULT_COLOR}" >&2;
    #echo -e "${LOG_INFO_COLOR}$(date +"%Y-%m-%d %H:%M:%S") | ${log_level} | $SCRIPTDIR/$SCRIPT_NAME | ${log_text_color} ${log_text} ${LOG_DEFAULT_COLOR}" >&2;
    echo -e "${LOG_INFO_COLOR}$(date +"%Y-%m-%d %H:%M:%S")|${log_level}|$PWD|$SCRIPTDIR/$SCRIPT_NAME ${log_text_color} ${log_text} ${LOG_DEFAULT_COLOR}" >&2;
    return 0;
}

log_info()      { log "$@"; }

log_speak()     {
    if type -P say >/dev/null
    then
        local easier_to_say="$1";
        case "${easier_to_say}" in
            studionowdev*)
                easier_to_say="studio now dev ${easier_to_say#studionowdev}";
                ;;
            studionow*)
                easier_to_say="studio now ${easier_to_say#studionow}";
                ;;
        esac
        say "${easier_to_say}";
    fi
    return 0;
}

log_success()   { log "$1" "SUCC" "${LOG_SUCCESS_COLOR}"; }
#log_error()     { log "$1" "ERROR" "${LOG_ERROR_COLOR}"; log_speak "$1"; }
log_error()     { log "$1" "ERROR" "${LOG_ERROR_COLOR}"; }
log_warning()   { log "$1" "WARN" "${LOG_WARN_COLOR}"; }
log_debug()     { log "$1" "DEBUG" "${LOG_DEBUG_COLOR}"; }
log_captains()  {
    if type -P figlet >/dev/null;
    then
        figlet -f computer -w 120 "$1";
    else
        log "$1";
    fi

    log_speak "$1";

    return 0;
}

run() {
    log "$*"
    eval "$@"
}


# ------------------------------------------
# Helper functions

base() {
    filename=${1##*/}
    if [[ $filename == *.gz ]]; then
        echo ${filename%.*.gz}
    else
        echo ${filename%.*}
    fi
}

is_target_remote() {
    IFS=":" read -r server path <<<"$1"
    test -n "$path"
}

makeabs() {
    for var in "$@"; do
        eval "$var=$(readlink -m "${!var}")"
    done
}

checkexists() {
    for var in "$@"; do
        [ -e ${!var} ] || { log_error "The $var '${!var}' does not exist"; exit 1; }
    done
}

get_if_remote() {
    local var
    tmpdir="$(mktemp -d)/remote_files" && mkdir -p "$tmpdir"
    for var in "$@"; do
        IFS=":" read -r server remotepath <<<"${!var}"
        if [ -n "$remotepath" ]; then # is remote
            log "$var is remote, fetch '${!var}'"
            mkdir -p "$tmpdir"
            run rsync -arv -e ssh "${!var}" "$tmpdir"
            if [[ $remotepath == *nhdr ]]; then  # if .nhdr get .raw file as well
                run rsync -arv -e ssh "${!var%.*}.raw.gz" "$tmpdir"
            fi
            filename="$(readlink -m "$tmpdir"/$(basename $remotepath))"
            [ ! -e $filename ] && { log_error "$var: Failed to get remote file '${!var}'"; exit 1; }
            eval "$var="$filename""
            log_success "Downloaded remote $var: '$filename'"
        else
            [ ! -e ${!var} ] && { log_error "The $var '${!var}' does not exist"; exit 1; }
            eval "$var=$(readlink -m "${!var}")"
            log "Found $var:'${!var}'"
        fi
    done
}

check_and_get_if_remote() {
    get_if_remote $@
}

rm_remotes() {
    log "Delete any temporary remote files"
    for var in "$@"; do
        parent_dir=$(dirname ${!var} | xargs basename)
        if [[ $parent_dir == remote_files ]]; then
            log "${!var} is a temporary remote file, delete it"
            run "rm -rf ${!var}"
            [[ ! ${!var} == *nhdr ]] || run "rm ${!var%.nhdr}.raw*"
        fi
    done
}

check_vars() {
    local var
    for var in "$@"; do
        if [ -z "${!var-}" ]; then 
            log_error "Set '${var}' in your shell environment (e.g. in your ~/.tcshrc or ~/.bashrc), \
or if running a 'redo' pipeline script, set it in '/path/to/your/project/SetUpData.sh'."
            exit 1
        #else
            #log "Found $var=${!var}"
        fi
    done
}

warp() {
    local moving=$1
    local fixed=$2
    local prefix=$3
    check_vars ANTSSRC ANTSPATH
    run $ANTSSRC/Scripts/antsIntroduction.sh -d 3 -i $moving -r $fixed -o $prefix -s MI 
    log_success "Made non-linear warp: '${prefix}Affine.txt', '${prefix}Warp.nii.gz'"
}


check_args() {
    local min_args=$1
    shift
    [ -n "${1-}" ] && [[ $1 == "-h" || $1 == "--help" ]] && usage 0
    [ $# -lt $min_args ] && usage 1
    return 0
}

assert_vars_are_set() {
    for var in "$@"; do
        [ -z "${!var-}" ] && { log_error "'$var' not set in ./SetUpData.sh"; exit 1; }
    done
    return 0
}

redo_ifchange_vars() {
    log "Update dependencies (may be remote): $*"
    assert_vars_are_set "$@"
    local local_deps=""
    for var in "$@"; do
        if [[ ${!var} == *:* ]]; then # is remote
            local server remotepath
            IFS=":" read -r server remotepath <<<"${!var}"
            log "Updating remote file: '${!var}'"
            run ssh $server "redo-ifchange "$remotepath""
        else
            eval "$var="$(readlink -m ${!var})""
            local_deps="$local_deps ${!var}"
        fi
    done
    redo-ifchange $local_deps
    log_success "Dependencies up to date"
}

varvalues() {
    local values=""
    for var in "$@"; do
        values="$values ${!var-}"
    done
    echo $values
}

printvars() {
    for var in "$@"; do
        if [ -n "${!var-}" ]; then
            printf "* %s=%s\n" $var ${!var}
        else 
            printf "* %s=\n" $var
        fi
    done
}

filter_remote() {
    local pred="$1"; shift
    IFS=":" read -r server _ <<<"$1"
    files=$(echo $@ | tr ' ' '\n' | cut -d":" -f2 | tr '\n' ' ')
    remote_cmd="`declare -f $pred`; for i in $files; do  $pred "\$i"  && echo \$i; done"
    #echo $remote_cmd
    ssh $server 'bash -s' <<<"$remote_cmd"
    exit
}

filter() {
    local pred="$1"; shift
    if [[ ${1} == *:* ]]; then
        filter_remote "$pred" $@
    else
        for i in $@; do
            $pred "$i" && echo "$i"
        done
    fi
}

map() {
    local fn="$1"; shift
    for i in $@; do
        eval "$fn $i"
    done
}

checkset_local_SetUpData() {
    [ ! -f SetUpData.sh ] && { echo "Run in directory with 'SetUpData.sh'"; usage; exit 1; } 
    [ -n "${case:-}" ] || { log_error "Set 'case' variable first before calling this function (util.sh:setupvars)"; exit 1; }
    source SetUpData.sh
    for var in $@; do
        if [ ! -n "${!var-}" ]; then
            echo "Set $var in 'SetUpData.sh' first."
            exit 1
        fi
    done
}

setupvars() {
    checkset_local_SetUpData $@
}

checkvars() {  
    check_vars $@
}

checkset_cases() {
    if [ -n "${cases-}" ]; then
        return
    fi

    if [ ! -n "${caselist-}" ]; then
        echo -e "Set variable 'caselist' (a text file) or 'cases' (a string of case ids) in 'SetUpData.sh', \nor pass them as arguments on the commandline."
        usage 1
    fi
     
    if [ ! -f "$caselist" ]; then
        echo "the caselist file '$caselist' (set in 'SetupData.sh' or passed in from the commandline) doesn't exist."
        exit 1
    fi

    cases=$(cat "$caselist" | awk '{print $1}')
}

setupcases() {
    checkset_cases $@
}

diff_and_exit() {
    if diff -q "$1" "$2" >/dev/null; then
        log_error ""$2" already exists (they are identical)"
    else
        log_error ""$2" already exists, not overwriting (they differ)"
    fi
    exit 0
}

start_logging() {
    exec &> >(tee "$1")  # pipe stderr and stdout to logfile as well as console
}

startlogging() {
    _tmplog=$(mktemp).log
    exec &> >(tee "$_tmplog")  # pipe stderr and stdout to logfile as well as console
}

stoplogging() {
    cp $_tmplog $1
    scrubcolors $1
}

printvarsOptional() {
    for var in "$@"; do
        if [ -n "${!var-}" ]; then
            printf "* %s=%s (optional)\n" $var ${!var}
        else 
            printf "* %s= (optional)\n" $var
        fi
    done
}

getUnsetVars() {
    local varsNotSet=""
    for var in $1; do
        [ -n "${!var-}" ] || varsNotSet="$varsNotSet $var"
    done
    echo ${varsNotSet# *}
}

# Requires 'inputvars' be set first
setupdo() {
    if [[ -e "$1" ]]; then
        echo "'$1' exists, delete it if you want to recompute it."
        mv $1 $3
        exit 0
    fi
    case=${2##*/}
    [ -n "${inputvars-}" ] || { log_error "Set 'inputvars' before calling this function (util.sh:setupdo)"; exit 1; }
    setupvars $inputvars
    printvars case 
    echo "Target:"
    echo "* $1"
    echo "Dependencies:"
    printvars $inputvars
    [ ! -n "${optvars-}" ] || printvarsOptional $optvars
    redo-ifchange $(varvalues $inputvars ${optvars-})
    log "Make '$1'"
}
