#!/usr/bin/env bash
set -eu

SCRIPTDIR=$( cd $(dirname "$0") ; pwd -P )
. "$SCRIPTDIR/loglib.sh"

usage () {
echo -e "\
Extracts the baseline of a DWI.

Usage:
    ${0##*/} [-m <dwimask>] -i <dwi> -o <out>

<dwi>       a nrrd volume (nrrd/nhdr)
<dwimask>   (optional) if given then the baseline is masked"
}

isValidNrrd() {
    nrrd=$1
    if [ ! -f "$nrrd" ]; then
        printf "$nrrd doesn't exist.\n"
        return  1
    elif [[ "${nrrd##*.}" != "nrrd" && "${nrrd##*.}" != "nhdr" ]]; then
        printf "$nrrd is not a nrrd file.\n"
        return 1
    fi
    header=$(unu head $nrrd 2>/dev/null)
    if test -z "$header"; then
        printf "$nrrd is a bad nrrd file.\n"
        return 1
    fi
    return 0
}

dwimask=""
[ $# -gt 0 ] || { usage; exit 1; }
while getopts "hi:o:m:" flag; do
    case "$flag" in
        h) usage; exit 1;;
        i) dwi=$OPTARG;;
        o) out=$OPTARG;;
        m) dwimask=$OPTARG;;
    esac
done
shift $((OPTIND-1))

[ -n "${dwi-}" -a -n "${out-}" ] || { usage; exit 1; }
isValidNrrd $dwi || { echo "The DWI is not a valid nrrd."; exit 1; }
[ -z "$dwimask" ] || isValidNrrd "$dwimask"

regex="DWMRI_gradient_\([0-9]*\):= *0\(\.0*\)\{0,1\}  *0\(\.0*\)\{0,1\}  *0\(\.0*\)\{0,1\}"
direction=$(unu head $dwi | sed -n "s|$regex|\1|p" | head -n 1)
log "Found baseline at gradient direction '$direction'"
if [ -n "$dwimask" ]; then
    run "unu slice -a 3 -p $direction -i $dwi | unu 3op ifelse -w 1 $dwimask - 0 | unu save -e gzip -f nrrd -o $out"
else
    run "unu slice -a 3 -p $direction -i "$dwi" | unu save -e gzip -f nrrd -o "$out""
fi

log_success "Made $out'"
