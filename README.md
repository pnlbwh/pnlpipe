# Prerequisites

* FSL
* FreeSurfer

# Setup

    git clone https://github.com/reckbo/pyppl.git
    export soft=<path/to/software/dir>

# Run

    make <caseid>  # runs default PNL pipeline

Or, you can run the setup steps individually:

    make software # makes $soft/BRAINSTools-bin-<hash>, etc.
    make inputpaths # makes _inputPaths.yml
    make <caseid> # runs default PNL pipeline

For PNL users using the cluster, you can run:

    make <caseid>-bsub4  # starts a 4 processor job on 'big-multi' queue
    make <caseid>-bsub8  # starts an 8 processor job on 'big-multi' queue
    make caselist # starts 8 processor job for each case in caselist.txt

# Advanced

You can customize the pipeline by editing the `makePipelines` function in
`pnlrun`. You can run more than one pipeline if you want to, for example, to
compare results using different parameters or algorithms.
