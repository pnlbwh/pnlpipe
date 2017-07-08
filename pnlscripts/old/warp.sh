#!/bin/bash -eu

SCRIPT=$(readlink -m "$(type -p "$0")")
SCRIPT_DIR=$(dirname "${SCRIPT}")      
source "$SCRIPT_DIR/util.sh"

usage() {
    echo -e "ANTS registration.  Default is non-linear warp.

Usage:
    ${0##*/} [-a|-r] [-f] [-x <outtransform>] [-s MI|CC] <moving> <fixed> <out>

-a     Affine only
-r     Rigid only
-x     Save transform as <outtransform>
-s     Similarity metric (default: 'MI')
-f     Fast registration, for debugging

"

}

FAST=false
LINEAR=false
DORIGID=""
DOFAST=""
METRIC="MI"
outtransform=""
while getopts "hfrax:s:" flag; do
    case "$flag" in
        h) usage 1; exit 0;;
        f) FAST=true;;
        r) LINEAR=true; DORIGID="--do-rigid";;
        a) LINEAR=true;;
        x) outtransform=$OPTARG;;
        s) METRIC=$OPTARG;; 
    esac
done
shift $((OPTIND-1))

[ $# -eq 3 ] || { usage; exit 1; }
inputvars="moving fixed out"
read -r $inputvars <<< "$@"
checkvars ANTSPATH
makeabs $inputvars 
checkexists moving fixed

startlogging 
printvars $inputvars ANTSPATH METRIC DORIGID 
$LINEAR || { checkvars ANTSSRC; printvars ANTSSRC; }

tmp=$(mktemp -d)
run pushd $tmp

pre=$(base $moving)-to-$(base $fixed)-

if $LINEAR; then
    $FAST && DOFAST="--number-of-affine-iterations 1"
    run ${ANTSPATH}/ANTS 3 -m $METRIC[$fixed,$moving,1,32] -i 0 -o $pre $DORIGID $DOFAST
    transform="${pre}Affine.txt"
    #if [ -n "$DORIGID" ];  then
        #outtransform="${out%.*}-rigid.txt"
    #else
        #outtransform="${out%.*}-affine.txt"
    #fi
else
    $FAST && DOFAST="-m 1x1x1"
    run $ANTSSRC/Scripts/antsIntroduction.sh -d 3 -i $moving -r $fixed -o $pre -s $METRIC $DOFAST
    transforms="${pre}Warp.nii.gz ${pre}Affine.txt"
    transform="${pre}warp.nii.gz"
    run "$ANTSPATH/ComposeMultiTransform 3 "$transform" -R "$fixed" $transforms || true"  
    #outtransform="${out%.*}-warp.nii.gz"
fi
log "Made '$transform'"

log "Transform moving to fixed space to make '$out'"
#run WarpImageMultiTransform 3 "$moving" "$out" -R "$fixed" "$transform" 
run $ANTSPATH/antsApplyTransforms -d 3 -i "$moving" -o "$out" -r "$fixed" -t "$transform"
if [[ $out == *nrrd ]]; then
    log "Output is nrrd, gzip it"
    run unu save -e gzip -f nrrd -i $out -o $out
fi

run popd

if [ -n "$outtransform" ]; then
    run mv $tmp/$transform $outtransform
    log_success "Made '$outtransform'"
fi

log_success "Made '$out'"
stoplogging "$out.log"
log_success "Made '$out.log'"

rm -rf $tmp
