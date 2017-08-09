*pnlpipe* is a framework for the authoring and running of file based data
processing pipelines, as well as for the automated installation of prerequisite
software packages. Once you have written a pipeline, and the installation
recipes for the software it relies on, you will be able to build all of its
dependent software automatically, and run it with one or more combinations of
parameters (including multiple software versions). It is efficient in that it
will only regenerate outputs when their upstream dependencies have changed.

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

Each path is a template that is parameterized by a case id. When a pipeline is
run for a particular a case id, it will use this dictionary to find the input
paths it needs. You only need to define this dictionary once.

## 2. Choose and run your pipelines


## 2. Run the pipelines

### Choose and setup a pipeline


Premade pipelines are in the `pnlpipe_pipelines` directory. For example, the
standard PNL pipeline is defined in `pnlpipe_pipelines/std.py`, and the EPI
correction pipeline is defined in `pnlpipe_pipelines/epi.py`. You can also get a
list of available pipelines by running `./pnlpipe -h`. As an example, we will
run the PNL standard pipeline, the one named `std`.

Before running a pipeline, we need to configure it. This involves two steps:
first, we need to specify its parameters, and second, we need to build the
software it requires.

To specify the parameters, we put them a [yaml](http://www.yaml.org/start.html)
configuration file, in this case called `pnlpipe_params/std.params`. To make a
default version of this file, run

    ./pnlpipe std init

This has the pipeline's default parameters. For the `std` pipeline, the
most important ones are the input keys, `inputDwiKey`, `inputT1Key`,
etc. These are the keys the pipeline uses to find its input data, by looking up
their paths in `pnlpipe_config.INPUT_KEYS`. For example, `inputDwiKey: [dwi]`
means that the pipeline will find its DWI input by looking up 'dwi' in
`INPUT_KEYS`. Likewise, `inputT1Key: [t1]` means that the pipeline will find its
T1w input by looking up 't1' in `INPUT_KEYS`.

Another important field is `caseid`; the default is `./caselist.txt`, which
means the pipeline will look in that file to find the case ids you want to use
with this pipeline. Make it by putting each case id on its own line.

More details on the parameters file are explained later on in this README.

Now you're ready to build the software needed by the pipeline. The required
software is determined by the parameters in `std.params` that end in '_version'
and '_hash'. Before building the software packages, you have to specify the
directory to install them to, and you do this by setting the environment
variable `$soft` (e.g. `export soft=path/to/software/dir`). Now build the
software by running

    ./pnlpipe std setup

If they already exist, nothing will build. You should see the results in
`$soft`, such as `$soft/BRAINSTools-bin-2d5eccb` and `$soft/UKFTractography-421a7ad`.


### Run and monitor the pipeline

Now you're read to run the pipeline:

    ./pnlpipe std run

This runs the `std` pipeline for every combination of parameters in `std.params`.
Since we're using the defaults, there is only combination of parameters.

You can get an overview of the pipeline and its progress by running

    ./pnlpipe std status

When the pipeline is done, you can generate a summary report:

    ./pnlpipe std summarize

This generates a `_data/std-tractmeasures.csv`, which has the measures of all wmql tracts
for every subject, and `_data/std-tractmeasures-summary.csv`, which is a summary of the wmql
tract measures along with the same measures from the INTRuST dataset as a way of comparison.

You can run any number of pipelines; for example, you could now run the EPI distortion
correction pipeline to compare it the standard one:

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


# Details

## 1. Define your inputs

Premade pipelines are in the `pnlpipe_pipelines` directory. For example, the
standard PNL pipeline is defined in `pnlpipe_pipelines/std.py`, and the
EPI correction pipeline is defined in `pnlpipe_pipelines/epi.py`.
You can also get a list of available pipelines by running `./pnlpipe -h`.

Once you've chosen your pipeline, the next step is to create a parameters file
that the pipeline will use.

    ./pnlpipe std init

This makes `pnlpipe_parameters/std.params` that has default parameters for this
pipeline.

    ./pnlpipe std init
    ./pnlpipe std setup  # builds the prerequisite software specified in `std.params`
    ./pnlpipe std run # runs the 'std' pipeline for all the parameter combinations in `std.params`
    ./pnlpipe std status  # shows an overview and the pipeline's progress
    ./pnlpipe std summarize  # creates a combined tract measures csv in _data

All output is saved to `_data/` (the default setting in `pnlpipe_config`).
The output for each case is saved in separate folders: `_data/<caseid>`.
