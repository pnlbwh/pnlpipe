*pnlpipe* is a framework for the authoring and running of file based data
processing pipelines, as well as for the automated installation of prerequisite
software packages. Once you have written a pipeline, and the installation
recipes for the software it relies on, you will be able run it with one or more
combinations of parameters (including multiple software versions), and be able
to build all of its dependent software automatically. It is efficient in that it
will only regenerate outputs when their upstream dependencies have changed, and
will share outputs between pipelines.

Included are some of the PNL's neuroimaging pipelines, written using a library
and scripts that you can use to extend and write new pipelines.


# Quick Walkthrough

## 1. Configure your input data

    cd /project/dir
    git clone https://github.com/reckbo/pnlpipe.git && cd pnlpipe
    export soft=/path/to/software/dir  # where software modules will be installed

Edit the paths of `INPUT_KEYS` in `pnlpipe_config.py` to point to your data. It will
look something like

    INPUT_KEYS = {
        'caseid_placeholder': '001',
        'dwi': '../001/001-dwi.nhdr',
        't1': '../001/001-t1w.nrrd'
        't2': '../001/001-t2w.nrrd'
    }

Each path is a template that is has a placeholder representing a case id (in
this example its '001'). Every pipeline is expected to accept a case id
parameter, and when run with a particular id, it will use this dictionary to
find the input paths it needs. You only need to define this dictionary once.

## 2. Run your pipelines

### Choose and setup a pipeline

Premade pipelines are in the `pnlpipe_pipelines` directory. For example, the
standard PNL pipeline is defined in `pnlpipe_pipelines/std.py`, and the EPI
correction pipeline is defined in `pnlpipe_pipelines/epi.py`. You can also get a
list of available pipelines by running `./pnlpipe -h`. As an example, we will
run the PNL standard pipeline, the one named `std`.

Before running a pipeline, we need to configure it. This involves two steps:
one, we need to specify its parameters, and two, we need to build the
software it requires.

To specify the parameters, we put them a [yaml](http://www.yaml.org/start.html)
configuration file, in this case called `pnlpipe_params/std.params`. To make a
default version of this file, run

    ./pnlpipe std init

This makes a parameter file with the pipeline's default parameters. For the
`std` pipeline, the most important ones are the input keys, `inputDwiKey`,
`inputT1Key`, etc. These are the keys the pipeline uses to find its input data,
by looking up their paths in `pnlpipe_config.INPUT_KEYS`. For example,
`inputDwiKey: [dwi]` means that the pipeline will find its DWI input by looking
up 'dwi' in `INPUT_KEYS`. Likewise, `inputT1Key: [t1]` means that the pipeline
will find its T1w input by looking up 't1' in `INPUT_KEYS`.  The reason it is
done this way is that if you happen to reorganize your data, you just have to
update your `pnlpipe_config.INPUT_KEYS`, and your parameters remain the same.

Another important field is `caseid`; the default is `./caselist.txt`, which
means the pipeline will look in that file to find the case ids you want to use
with this pipeline. Make it by putting each case id on its own line.

You will notice that the parameter values are wrapped in square brackets. This
is because you can specify more than one value for each parameter. For example,
if you wanted to run the `std` pipeline using a DWI masking bet threshold of 0.1
as well as a 0.15, you would write: `bet_threshold: [0.1, 0.15]`. For more
details on specifying multiple parameter combinations, see further down in this
README.

Now you're ready to build the software needed by the pipeline. The required
software is determined by the parameters that end in '_version' and '_hash' (a
Github commit hash). Before building the software packages, you need to specify
the directory to install them to, and you do this by setting a global
environment variable called `$PNLPIPE_SOFT` (e.g. `export PNLPIPE_SOFT=path/to/software/dir`).
Now build the software by running

    ./pnlpipe std setup

(if any of the software packages already exist, they will not rebuild). You should now
see the results in `$PNLPIPE_SOFT`, such as `BRAINSTools-bin-2d5eccb/` and
`UKFTractography-421a7ad/`.


### Run and monitor the pipeline

Now you're read to run the pipeline:

    ./pnlpipe std run

This runs the `std` pipeline for every combination of parameters in
`std.params`. Since we're using the defaults, there is only one combination of
parameters per case id.

You can get an overview of the pipeline and its progress by running

    ./pnlpipe std status

This prints the pipeline's parameters, the input and output paths, and how many
case ids are processed thus far.

When the pipeline is done, you can generate a summary report:

    ./pnlpipe std summarize

This makes `_data/std-tractmeasures.csv`, a csv of all wmql tract measures
across all subjects, and `_data/std-tractmeasures-summary.csv`, a summary csv of
wmql tract measures together with their counterparts from the INTRuST dataset as
a way of comparison.

You're not limited to running one pipeline, you can run any number of the
pipelines available. For example, you could now run the EPI distortion
correction pipeline in order to compare its results to that of the standard one:

    ./pnlpipe epi init
    # edit pnlpipe_params/epi.params
    ./pnlpipe epi setup
    ./pnlpipe epi run
    ./pnlpipe epi summarize

You will then see the files

    _data/std-tractmeasures.csv
    _data/std-tractmeasures-summary.csv
    _data/epi-tractmeasures.csv
    _data/epi-tractmeasures-summary.csv



# Listing output

Every pipeline gives a short name for some, usually all, of its outputs. You can
see these names when you run `./pnlpipe <pipeline> status` (or by inspecting the
pipeline's `make_pipeline` function in `pnlpipe_pipelines/<pipline>.py`). For
example, the `std` pipeline describes `dwied` as an eddy current corrected
DWI, and shows its output template path as `_data/<caseid>/DwiEd-<caseid>-...nrrd`.
To list the actual output paths of the eddy corrected DWI's for all your case ids, use the `ls` subcommand:

    pnlpipe std ls dwied

This lists all existing output.  If you'd like to get a list of missing
output, use the `-x` flag:

    ./pnlpipe std ls -x dwied

For all output, existing and missing, use `-a`:

    ./pnlpipe std ls -a dwied

Sometimes you just want the list of case ids for which a particular
output exists (or is missing), or perhaps you want the case ids alongside
their output paths.  You can do that as follows:

   pnlpipe std ls -s dwied # prints <caseid> for existing paths
   pnlpipe std ls -c dwid  # prints <caseid>,<path> for existing paths

You can combine flags together. To get the csv of all missing Freesurfer
subject directories, you would run

    ./pnlpipe std ls -cx fs

The `ls` command helps you inspect your data by piping the results to other
commands.  Say you want to get the space directions of all your eddy
corrected DWI's:

    ./pnlpipe std ls dwied | unu head | grep 'space directions'


# PNL: Running on the cluster

The PNL uses a high performance computing cluster for most of its data processing.
The cluster uses [LSF](https://en.wikipedia.org/wiki/Platform_LSF) to manage batch
processing, and *pnlpipe* provides a Makefile that allows you to easily submit jobs
to this system to run your pipelines.

First, edit `Makefile` and replace `std` in the line `PIPE := std` to the name
of the pipeline you wish to run. Now you can submit pipeline jobs for individual
case ids like so:

    make 001-bsub8 002-bsub8 003-bsub8

This submits an 8 core lsf job for each of the case ids `001`, `002`, and `003`.
If resources are limited it might be better to ask for 4 core jobs:

    make 001-bsub4 002-bsub4 003-bsub4

For a large case list, this method is too tedious, and it's possible that you accidentally submit
a job for a case id that's already in the queue or being processed.  A better way is to
run

    make caselist-bsub8  # or, make caselist-bsub4

This will iterate over each case id in `caselist.txt` and submit an 8 core job
to the LSF system, but only if that case id is not already running (it uses the
LSF command `bjobs` to figure out what's currently running). If your caselist is
named something other than `caselist.txt`, edit the `Makefile` and modify the
line `CASELIST := caselist.txt` to point to your file.

An alternative to modifying the Makefile is to set its variables on the command
line:

    make PIPE=std CASELIST=caselist2.txt caselist-bsub8


# Multiple Parameter Combinations
