# Prerequisites

* FSL
* FreeSurfer

# Install

    cd /project/dir
    git clone https://github.com/reckbo/pyppl.git

# Configure Pipeline

    export soft=<path/to/software/dir>  # where software will be installed
    # make $soft/BRAINSTools-bin-<hash>, $soft/UKFTractography-<hash>,
    # $soft/tract_querier-<hash>, $soft/trainingDataT1AHCC
    make software
    make paths # make _inputPaths.yml

# Run

    make <caseid>  # runs standard PNL pipeline

For PNL users using the cluster, you can run:

    make <caseid>-bsub4  # starts a 4 processor job on 'big-multi' queue
    make <caseid>-bsub8  # starts an 8 processor job on 'big-multi' queue
    make caselist # starts 8 processor job for each case in caselist.txt

# Epi Correction

By default, running `make` runs the standard PNL pipeline by calling

    ./pyppl std <caseid>

To run the PNL pipeline with EPI correction, use this command instead:

    ./pyppl epi <caseid>

For convenience you can edit `RUN` at the top of the `Makefile`
and replace `std` with `epi` and run the pipeline as `make <caseid>`.


# Advanced

You can make your own custom pipelines by editing `Custom` in `pyppl`. You
could, for example, create a set of pipelines with different parameters or
algorithms in order to compare their results. Once you've defined your
pipeline(s), run it as

    ./pyppl custom <caseid>

As with epi correction, you can edit `RUN` at the top of the `Makefile`
and replace `std` with `custom` so that you can run your custom pipeline(s)
as `make <caseid>`.
