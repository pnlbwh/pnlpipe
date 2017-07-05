#!/usr/bin/env bash
#
# dependencies:
# * util.sh
# * warp.sh (todo: replace this with antsRegistrationSyn.sh)
# * bse.sh
# * mask
# * $FREESURFER_HOME
# * $ANTSPATH
# * $ANTSSRC (needed by warp.sh)

set -eu
SCRIPT=$(readlink -m $(type -p $0))
SCRIPTDIR=${SCRIPT%/*}
source "$SCRIPTDIR/util.sh"

makeAbsolute() {
    for var in "$@"; do
        eval "$var=$(readlink -m "${!var}")"
    done
}

assertPathsExist() {
    for var in "$@"; do
        [ -e "${!var}" ] || { log_error "The $var '${!var}' does not exist"; exit 1; }
    done
}

assertVarsAreSet() {
    for var in "$@"; do
        [ -n "${!var-}" ] || { echo "Value for --$var missing"; usage; exit 1; }
    done
}

prettyPrint() {
    for var in "$@"; do
        if [ -n "${!var-}" ]; then
            printf "* %s=%s\n" $var ${!var}
        else 
            printf "* %s=\n" $var
        fi
    done
}

HELP="
Usage:

   ${0##*/} --fsdir <freesurfer_directory> --dwi <dwi> --dwimask <dwimask> --t2 <T2> [--t2mask <T2mask>] --t1 <T1> --t1mask <T1mask> -o <output_dir>

where <dwi> and <dwimask> are nrrd/nhdr files
"

export SUBJECTS_DIR=

[ $# -gt 0 ] || { usage; exit 1; }

while getopts "ho:-:" OPTION; do
    case $OPTION in
        h) usage; exit 1;;
        o) output_dir=$OPTARG ;;
        -) case "$OPTARG" in
            fsdir) fsdir="${!OPTIND}"; OPTIND=$(( $OPTIND + 1 )) ;;
            dwi) dwi="${!OPTIND}"; OPTIND=$(( $OPTIND + 1 )) ;;
            dwimask) dwimask="${!OPTIND}"; OPTIND=$(( $OPTIND + 1 )) ;;
            t1) t1="${!OPTIND}"; OPTIND=$(( $OPTIND + 1 )) ;;
            t1mask) t1mask="${!OPTIND}"; OPTIND=$(( $OPTIND + 1 )) ;;
            t2) t2="${!OPTIND}"; OPTIND=$(( $OPTIND + 1 )) ;;
            t2mask) t2mask="${!OPTIND}"; OPTIND=$(( $OPTIND + 1 )) ;;
            *)
                if [ "$OPTERR" = 1 ] && [ "${optspec:0:1}" != ":" ]; then
                    echo "Unknown option --${OPTARG}" >&2
                fi
                ;;
        esac;;
        *)
            if [ "$OPTERR" != 1 ] || [ "${optspec:0:1}" = ":" ]; then
                echo "Non-option argument: '-${OPTARG}'" >&2
            fi
            ;;
    esac
done

varsRequired="fsdir dwi dwimask t1 t1mask t2 output_dir"
varsEnv="FREESURFER_HOME ANTSPATH ANTSSRC"

assertVarsAreSet $varsRequired
makeAbsolute $varsRequired 
assertPathsExist ${varsRequired% *} $varsEnv
if [ -n "${t2mask-}" ]; then
    makeAbsolute t2mask
    assertPathsExist t2mask
fi

log "Inputs:"
prettyPrint $varsRequired t2mask $varsEnv

startlogging

log "Make and change to output directory"
run "mkdir $output_dir" || { log_error "$output_dir already exists, delete it or choose another output folder name"; exit 1; }
run pushd $output_dir >/dev/null

if [ -z "${t2mask-}" ]; then
    t2mask=t2mask.nrrd
    $SCRIPTDIR/make_rigid_mask.sh $t1mask $t1 $t2 $t2mask
fi

mri=$fsdir/mri
log "Make brain.nii.gz and wmparc.nii.gz from their mgz versions"
#$fsbin/mri_convert -rt nearest --in_type mgz --out_type nii --out_orientation LPI $mri/wmparc.mgz $mri/wmparc.nii.gz
#$fsbin/mri_convert -rt nearest --in_type mgz --out_type nii --out_orientation LPI $mri/brain.mgz $mri/brain.nii.gz
run $FREESURFER_HOME/bin/mri_vol2vol --mov $mri/brain.mgz --targ $mri/brain.mgz --regheader --o brain.nii.gz
run $FREESURFER_HOME/bin//mri_label2vol --seg $mri/wmparc.mgz --temp $mri/brain.mgz --o wmparc.nii.gz --regheader $mri/wmparc.mgz
log_success "Made 'brain.nii.gz' and 'wmparc.nii.gz'"

log "Make masked T2"
maskedt2=$(base $t2)-masked.nrrd
run $SCRIPTDIR/mask "$t2" "$t2mask" $maskedt2
log_success "Made masked T2: '$maskedt2'"

log "Make masked T1"
maskedt1=$(base $t1)-masked.nrrd
run $SCRIPTDIR/mask "$t1" "$t1mask" $maskedt1
log_success "Made masked T1: '$maskedt1'"

log "Make masked baseline"
bse=$(basename "$dwi")
bse="${bse%%.*}-bse.nrrd"
maskedbse=$(basename ${bse%%.*}-masked.nrrd)
run $SCRIPTDIR/bse.sh -m $dwimask -i $dwi -o $maskedbse
#$SCRIPTDIR/center.py -i "$maskedbse" -o "$maskedbse"
log_success "Made masked baseline: '$maskedbse'"

log "Upsample masked baseline to 1x1x1: "
maskedbse1mm=$(basename ${maskedbse%%.*}-1mm.nii.gz)
run $ANTSPATH/ResampleImageBySpacing 3 $maskedbse $maskedbse1mm 1 1 1 
log_success "Made masked baseline: '$maskedbse1mm'"

log "Compute rigid transformation from brain.nii.gz to T1"
#rigidtransform brain.nii.gz $maskedt1 "fs-to-t1-rigid.txt"
run $SCRIPTDIR/warp.sh -x fs-to-t1-rigid.txt -r brain.nii.gz $maskedt1 fs-in-t1.nrrd  # '-x': makes fs-to-t1-rigid.txt

log "Compute rigid transformation from masked T1 to masked T2"
#rigidtransform $maskedt1 $maskedt2 "t1-to-t2-rigid.txt"
run $SCRIPTDIR/warp.sh -x t1-to-t2-rigid.txt -r $maskedt1 $maskedt2 t1-in-t2.nrrd  # '-x': makes t1-to-t2-rigid.txt

log "Compute warp from T2 to DWI baseline"
#warp $maskedt2 $maskedbse1mm "t2-to-bse-"
run $SCRIPTDIR/warp.sh -x t2-to-bse-warp.nii.gz -s CC $maskedt2 $maskedbse1mm t2-in-bse.nrrd  # '-x': makes t2-to-bse-warp.nii.gz
#run mv t2-to-bse-deformed.nii.gz t2-in-bse.nii.gz 

log "Apply transformations to wmparc.nii.gz to create wmparc-in-bse.nii.gz"
#run $ANTSPATH/antsApplyTransforms -d 3 -i wmparc.nii.gz -o wmparc-in-bse.nrrd -r "$maskedbse" -n NearestNeighbor -t t2-to-bse-Warp.nii.gz t2-to-bse-Affine.txt t1-to-t2-rigid.txt fs-to-t1-rigid.txt
run $ANTSPATH/antsApplyTransforms -d 3 -i wmparc.nii.gz -o wmparc-in-bse.nrrd -r "$maskedbse1mm" -n NearestNeighbor -t t2-to-bse-warp.nii.gz t1-to-t2-rigid.txt fs-to-t1-rigid.txt
run ConvertBetweenFileFormats wmparc-in-bse.nrrd wmparc-in-bse.nrrd short
log_success "Made 'wmparc-in-bse.nrrd'"

popd

stoplogging "$output_dir/log"
#log_success "Made ' $(readlink -f "$output_dir")' and '$(readlink -f "$output_dir"/wmparc-in-bse.nrrd)'"
log_success "Made '$output_dir' and '$output_dir/wmparc-in-bse.nrrd'"
