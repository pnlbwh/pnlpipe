PYPPLDIR=$(readlink -m ${BASH_SOURCE[0]})
PYPPLDIR=${PYPPLDIR%/*}

type -P "conda" && source activate pyppl || \
        echo "Conda not found in path, so not loading python environment.
(If using virtualenv, run 'make venv; source activate _venv/bin/activate';
if you just haven't made the conda environment yet, run 'make conda')"

BRAINSTOOLS=__BRAINSTOOLS__
# UKFTRACTOGRAPHY=__UKFTRACTOGRAPHY__
TRACT_QUERIER=__TRACT_QUERIER__

export PATH=$PYPPLDIR/pnlscripts:$TRACT_QUERIER/scripts:$UKFTRACTOGRAPHY:$BRAINSTOOLS:$PATH
export PYTHONPATH=$TRACT_QUERIER:PYTHONPATH

echo "Added to PATH:"
echo $PNLSCRIPTS/pnlscripts
echo $BRAINSTOOLS
# echo $UKFTRACTOGRAPHY
echo $TRACT_QUERIER/scripts

echo "Added to PYTHONPATH:"
echo $TRACT_QUERIER


# Exports the key value pairs in paths.yml if it exists
# E.g.
#    withpaths
#    unu head $t1
#    fslinfo $dwihcp
# (Would work nicely with direnv)
withpaths() {
    if [ -f paths.yml ]; then
        yml=paths.yml
    elif [ -f _inputPaths.yml ]; then
        yml=_inputPaths.yml
    else
        echo "paths.yml or _paths.yml doesn't exist";
        return
    fi
    echo "Found paths.yml, exporting variables..."
    while IFS=":" read -r key val; do
        path="$(echo -e "${val}" | sed -e 's/^[[:space:]]*//')"
        echo "export $key=$path"
        export $key=$path
    done < $yml
}
