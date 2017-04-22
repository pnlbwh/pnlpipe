if [ -z "${SCRIPTDIR-}" ]; then
    SCRIPTDIR=$( cd $(dirname "$0") ; pwd -P )
fi
SCRIPT=$SCRIPTDIR/${0##*/}

if [ -z "${INTERACTIVE_MODE-}" ]; then
    INTERACTIVE_MODE="on"
fi

if [[ "${INTERACTIVE_MODE}" == "off" ]]; then
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
    echo -e "${LOG_INFO_COLOR}$(date +"%Y-%m-%d %H:%M:%S")|${log_level}|$PWD|$SCRIPTDIR/$SCRIPT ${log_text_color} ${log_text} ${LOG_DEFAULT_COLOR}" >&2;
    return 0;
}

log_info()      { log "$@"; }
log_success()   { log "$1" "SUCC" "${LOG_SUCCESS_COLOR}"; }
#log_error()     { log "$1" "ERROR" "${LOG_ERROR_COLOR}"; log_speak "$1"; }
log_error()     { log "$1" "ERROR" "${LOG_ERROR_COLOR}"; }
log_warning()   { log "$1" "WARN" "${LOG_WARN_COLOR}"; }
log_debug()     { log "$1" "DEBUG" "${LOG_DEBUG_COLOR}"; }

run() {
    log "$*"
    eval "$@"
}
