OUTDIR = '_data' # pnlpipe/_data, alternatively you may specify an absolute path

# diverting the temporary directory to avoid space shortage in shared /tmp
# set to None to write to default /tmp
import os
TMPDIR = os.path.join(os.environ['HOME'],'tmp')
# if the path you are setting doesn't exist, it will point to default /tmp
TMPDIR = TMPDIR if os.path.exists(TMPDIR) else '/tmp'

# an input path is found by looking up its key in INPUT_KEYS
# value of each key is returned after substituting a caseid"
# give proper paths for one caseid as your files are stored in your system
INTRuST = {
    'caseid_placeholder': '003_GNX_007',
    'dwi': '/data/pnl/INTRuST/003_GNX_007/raw/003_GNX_007-dwi.nhdr',
    't1': '/data/pnl/INTRuST/003_GNX_007/raw/003_GNX_007-t1w.nhdr',
    't2': '/data/pnl/INTRuST/003_GNX_007/raw/003_GNX_007-t2w.nhdr'
}
INPUT_KEYS = INTRuST

# every time you input a different set of std.params/epi.params,
# give the following a different name
# so you are able to compare tract-summaries among parameters
PROJECT_ALG_NAME = 'usrAlg '

# number of processors to use, if other processes in your computer
# becomes sluggish/you run into memory error, reduce NCPU
# atlas.py, eddy.py, and wmql.py make use of python multi-processing capability
NCPU = '8'