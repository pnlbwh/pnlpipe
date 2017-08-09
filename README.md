Pnlpipe is a framework for programmatically authoring file based data pipelines.
It can run using many combination of parameters, automatically builds prerequisite
software, records data provenance, and prints status reports.  It comes prepopulated
with some of the PNL's neuroimaging pipelines, written using a library and scripts that
you can use to extend or write new pipelines.

# Install and Setup

    cd /project/dir
    git clone https://github.com/reckbo/pnlpipe.git && cd pnlpipe
    export soft=<path/to/software/dir>  # where software modules will be installed
    source pnlpipe.bash_completion # allows tab completion of subcommands


# Quick Example

Premade pipelines are in the `pnlpipe_pipelines` directory. For example, the
standard PNL pipeline is defined in `pnlpipe_pipelines/std.py`, and the
DWI EPI correction pipeline is defined in `pnlpipe_pipelines/epi.py`.

First, add your input file paths to the `INPUT_KEYS` dictionary in `pnlpipe_config.py`.
It will look like this:

    INPUT_KEYS = {
        'caseid_placeholder': '001',
        'dwi': '../001/001-dwi.nhdr',
        't1': '../001/001-t1w.nrrd'
        't2': '../001/001-t2w.nrrd'
    }

Each path is a template that is parameterized by a caseid.  When a pipeline is run
on a caseid, it will use this dictionary to find the input paths it needs.
You only need to define this dictionary once.

Now, you choose one of the pipelines to run on your data.  You can get a list
of pipelines by running


    ./pnlpipe std init # makes default parameter file `pnlpipe_params/std.params`, edit to change parameters
    ./pnlpipe std setup  # builds the prerequisite software specified in `std.params`
    ./pnlpipe std run # runs the 'std' pipeline for all the parameter combinations in `std.params`
    ./pnlpipe std status  # shows an overview and the pipeline's progress
    ./pnlpipe std summarize  # creates a combined tract measures csv in _data

All output is saved to `_data/` (the default setting in `pnlpipe_config`).
The output for each case is saved in separate folders: `_data/<caseid>`.
