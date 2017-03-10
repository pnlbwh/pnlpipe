# Prerequisites

* FSL
* FreeSurfer

# Install

    cd /project/dir
    git clone https://github.com/reckbo/pnlpipe.git
    cd pnlpipe
    export soft=<path/to/software/dir>  # where software will be installed

# Examaple

    ./pipe init  # define your input paths, makes inputPaths.yml

Run the standard PNL pipeline:

    ./pipe std init # set parameters for 'std' pipeline, makes 'params.std'
    ./pipe std make # builds 'std' pipeline's prequisite software
    ./pipe std run # runs the 'std' pipeline with your parameters

To run the EPI correctin pipeline, replace `std` with `epi`.

# Details

TODO

# Advanced

You can make a custom pipeline by creating a file `pipelines/pipeline_<name>.py`
and run it the same way you run the standard and EPI correction pipelines:

    ./pipe <name> init
    ./pipe <name> make
    ./pipe <name> run
