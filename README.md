# Prerequisites

* FSL
* FreeSurfer

# Install

    cd /project/dir
    git clone https://github.com/reckbo/pnlpipe.git && cd pnlpipe
    export soft=<path/to/software/dir>  # where software will be installed

# Example

Run the standard PNL pipeline:

    ./pipe init  # define your input paths for this project, makes 'inputPaths.yml'
    ./pipe std init # set parameters for 'std' pipeline, makes 'params.std'
    # Edit params.std and fill in mandatory fields (i.e. replace '*mandatory*' strings)
    ./pipe std make # builds the prerequisite software specified in 'params.std'
    ./pipe std run # runs the 'std' pipeline using 'params.std'

All output will be generated in `_data/<caseid>/`, including the final tract
measures csv. To run the EPI correction pipeline, replace `std` with `epi`.

# Details

## How it works

TODO
* explain generally how it works
* explain how params yaml can specify many parameters using lists
* explain how to add custom pipeline and software modules
