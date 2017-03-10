# Exports the key value pairs in paths.yml if it exists
# E.g.
#    withpaths
#    unu head $t1
#    fslinfo $dwihcp
# (Would work nicely with direnv)
withpaths() {
    dir='.'
    if [ -n "${1}" ]; then
        dir=$1
    fi
    if [ -f "$dir/paths.yml" ]; then
        yml="$dir/paths.yml"
    elif [ -f "$dir/_inputPaths.yml" ]; then
        yml="$dir/_inputPaths.yml"
    else
        echo "$dir/paths.yml or $dir/_inputPaths.yml doesn't exist";
        return
    fi
    echo "Found $dir/paths.yml, exporting variables..."
    while IFS=":" read -r key val; do
        path="$(echo -e "${val}" | sed -e 's/^[[:space:]]*//')"
        echo "export $key=$dir/$path"
        export $key=$dir/$path
    done < $yml
}

base=$(readlink -m ${BASH_SOURCE[0]}) && base=${base%/*}

type -P "conda" && source activate pyppl || \
        echo "Conda not found in path, so not loading python environment.
(If using virtualenv, run 'make venv; source activate _venv/bin/activate';
if you just haven't made the conda environment yet, run 'make conda')"

BRAINSTOOLS=__BRAINSTOOLS__
TRACT_QUERIER=__TRACT_QUERIER__

export PATH=${base}/pnlscripts:${TRACT_QUERIER}/scripts:$UKFTRACTOGRAPHY:$BRAINSTOOLS:$PATH
export PYTHONPATH=$TRACT_QUERIER:$PYTHONPATH
export ANTSPATH=$BRAINSTOOLS

echo "Added to PATH:"
echo $base/pnlscripts
echo $BRAINSTOOLS
# echo $UKFTRACTOGRAPHY
echo $TRACT_QUERIER/scripts

echo "Added to PYTHONPATH:"
echo $TRACT_QUERIER

withpaths $base
