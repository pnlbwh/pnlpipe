(Under development)

# PNL Prerequisites

* FSL
* FreeSurfer

# Install

    cd /project/dir
    git clone https://github.com/reckbo/pnlpipe.git && cd pnlpipe
    export soft=<path/to/pp_software/dir>  # where software modules will be installed

# Quick Example

Run the standard PNL pipeline:

    ./pipe std init # set parameters for 'std' pipeline, makes `pnlpipe_params/std.params`

    # Add your parameters to std.params, or leave the defaults

    ./pipe std make # builds the prerequisite software specified in `std.params`

    ./pipe std run # runs the 'std' pipeline for all the parameter combinations in `std.params`

All output will be generated in `_data/<caseid>/`, including the final tract
measures csv. To run the EPI correction pipeline, replace `std` with `epi`.
