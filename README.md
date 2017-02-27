# Prerequisites

* FSL
* FreeSurfer

# Setup

    git clone https://github.com/reckbo/pyppl.git --recursive
    export soft=<path/to/software/dir>
    make software # makes BRAINSTools, tract_querier, UKFTractography, T1w mask training set

# Run

    ./pnlmake [switches]  # Makes _paths.yml, a dictionary of template paths to your input data
    ./pnlrun [-w target] caseids... # Runs the pipeline(s)

For PNL users using the cluster, you can run:

    make <caseid>-bsub4  # starts a 4 processor job on 'big-multi' queue
    make <caseid>-bsub8  # starts an 8 processor job on 'big-multi' queue
    make caselist # starts 8 processor job for each case in caselist.txt

# Advanced

You can customize the pipeline by editing the `makePipelines` function in
`pnlrun`. You can run more than one pipeline if you want to, for example, to
compare results using different parameters or algorithms.
