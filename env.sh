base=$(readlink -m ${BASH_SOURCE[0]}) && base=${base%/*}
export PATH=$base:$base/pnlscripts:$PATH
source $base/pnlpipe.bash_completion
