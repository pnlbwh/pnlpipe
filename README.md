![](Misc/pnl-bwh-hms.png)

[![DOI](https://zenodo.org/badge/doi/10.5281/zenodo.2584271.svg)](https://doi.org/10.5281/zenodo.2584271) [![Python](https://img.shields.io/badge/Python-3.6-green.svg)]() [![Platform](https://img.shields.io/badge/Platform-linux--64%20%7C%20osx--64-orange.svg)]()

Developed by Tashrif Billah, Ryan Eckbo, Sylvain Bouix, and Isaiah Norton, Brigham and Women's Hospital (Harvard Medical School).

<!-- markdown-toc start - Don't edit this section. Run [gh-md-toc](https://github.com/ekalinin/github-markdown-toc to generate toc again -->

Table of Contents
=================

   * [Table of Contents](#table-of-contents)
   * [Citation](#citation)
   * [Introduction](#introduction)
   * [Installation](#installation)
      * [1. Install prerequisites](#1-install-prerequisites)
         * [Check system architecture](#check-system-architecture)
         * [Python 3](#python-3)
         * [FSL](#fsl)
         * [FreeSurfer](#freesurfer)
      * [2. Install pipeline](#2-install-pipeline)
      * [3. Tests](#3-tests)
      * [4. whitematteranalysis package](#4-whitematteranalysis-package)
   * [Running](#running)
      * [Running individual scripts](#running-individual-scripts)
         * [1. Configure your environment](#1-configure-your-environment)
         * [2. Temporary directory](#2-temporary-directory)
         * [3. Source individual software module](#3-source-individual-software-module)
      * [Running the pipelines](#running-the-pipelines)
         * [1. Configure your environment](#1-configure-your-environment-1)
         * [2. Configure your input data](#2-configure-your-input-data)
         * [3. Multiprocessing](#3-multiprocessing)
      * [3. Analyze data](#3-analyze-data)
   * [Tests](#tests)
   * [Pipeline scripts overview](#pipeline-scripts-overview)
   * [DICOM to NRRD](#dicom-to-nrrd)
   * [Run and monitor](#run-and-monitor)
   * [Listing your pipeline's output](#listing-your-pipelines-output)
   * [Setup](#setup)
   * [Advanced options](#advanced-options)
      * [1. Parameters](#1-parameters)
         * [Multiple Parameter Combinations](#multiple-parameter-combinations)
         * [Lists of parameter values](#lists-of-parameter-values)
         * [Lists of parameter dictionaries](#lists-of-parameter-dictionaries)
         * [Running and listing specific parameter combinations](#running-and-listing-specific-parameter-combinations)
      * [2. Shell environment](#2-shell-environment)
         * [Pipeline shell environment](#pipeline-shell-environment)
         * [Ad-hoc shell environment](#ad-hoc-shell-environment)
         * [Global bashrc](#global-bashrc)
      * [3. PNL: Running on the cluster](#3-pnl-running-on-the-cluster)
      * [4. Installing software without using pipeline](#4-installing-software-without-using-pipeline)
      * [5. Writing your own pipelines](#5-writing-your-own-pipelines)
   * [Issues](#issues)
      * [Known errors](#known-errors)
         * [1. error setting certificate verify locations](#1-error-setting-certificate-verify-locations)
      * [Support](#support)


<!-- markdown-toc end -->

# Citation

If this pipeline is useful in your research, please cite as below:

Billah, Tashrif*; Eckbo, Ryan*; Bouix, Sylvain; Norton, Isaiah;
Processing pipeline for anatomical and diffusion weighted images,
https://github.com/pnlbwh/pnlpipe, 2018, DOI: 10.5281/zenodo.2584271

*denotes equal first authorship

# Introduction

*pnlpipe* is a Python-based framework for processing anatomical (T1, T2) and diffusion weighted images.
It is prepackaged with some of the [PNL](http://pnl.bwh.harvard.edu)'s neuroimaging pipelines that are
based on a library and scripts you can use to write new pipelines. Each of the pipelines accepts a
caselist of images to be analyzed and produces organized output with proper logging. The framework
also supports execution of individual scripts. A pipeline is a directed acyclic graph (DAG) of dependencies.
The following diagram depicts functionality of the *std* (standard) pipeline where
each node represents an output, and the arrows represent dependencies:

![](pnlpipe_doc/dag.png)

Dependencies:

* unu
* freesurfer
* ANTs
* numpy
* FSL


# Installation

## 1. Install prerequisites

Python 3, FreeSurfer>=5.0.3 and FSL (ignore the one(s) you have already):

### Check system architecture

    uname -a # check if 32 or 64 bit

### Python 3

Download [Miniconda Python 3.6 bash installer](https://conda.io/miniconda.html) (32/64-bit based on your environment):
    
    sh Miniconda3-latest-Linux-x86_64.sh -b # -b flag is for license agreement

Activate the conda environment:

    source ~/miniconda3/bin/activate # should introduce '(base)' in front of each line

### FSL

Follow the [instruction](https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FslInstallation) to download and install FSL.

Make sure to do the patch for *imcp/imglob/immv errors* from the instruction.


    
### FreeSurfer
    
Follow the [instruction](https://surfer.nmr.mgh.harvard.edu/fswiki/DownloadAndInstall) to download and install FreeSurfer >= 5.0.3
After installation, you can check FreeSurfer version by typing `freesurfer` on the terminal.



## 2. Install pipeline

Now that you have installed the prerequisite software, you are ready to install the pipelines (std, epi, hcp):

    git clone --recurse-submodules https://github.com/pnlbwh/pnlpipe.git && cd pnlpipe
    git checkout py3-compatible         # temporarily we are using py3-compatible branch
    conda env create -f python_env/environment36.yml
    conda activate pnlpipe3             # should introduce '(pnlpipe3)' in front of each line
    mkdir soft_dir                      # 'soft_dir' is where pipeline dependencies will be installed
    export PNLPIPE_SOFT=`pwd`/soft_dir
    ./pnlpipe std init                  # makes default parameter file: pnlpipe_params/std.params
    ./pnlpipe std setup                 # builds pipeline dependencies specified in std.params

Afterwards, you may also install the epi pipeline:

    ./pnlpipe epi init                  # makes default parameter file: pnlpipe_params/epi.params
    ./pnlpipe epi setup                 # builds pipeline dependencies specified in epi.params


A little elaborate instruction is given in [Setup](#setup).


## 3. Tests

A small test data is provided with each release. You should download test data as follows:
    
    cd pnlpipe
    wget https://github.com/pnlbwh/pnlpipe/releases/download/v2.1.0/test_data.zip
    unzip test_data.zip # should unzip to INTRuST folder
    cp INTRuST/pnlpipe_config.py .
    cp INTRuST/caselist.txt .
    
Then, as you would run the pipeline (see [Running](#running)):

    ./pnlpipe std run

During pipeline execution, you can check the progress:

    ./pnlpipe std status
    
Also, at the end of execution, you can check the summary:
    
    ./pnlpipe std summarize


## 4. whitematteranalysis package

If you would like to analyze quality of tractography fibers, you should also install [whitematteranalysis](https://github.com/SlicerDMRI/whitematteranalysis) by Lauren O'Donnell. 
While *pnlpipe* is based on *Python 3*, `whitematteranalysis` requires *Python 2* interpreter. 
To install `whitematteranalysis`, open a new terminal and run the following set of commands:
    
    # download proper binay for your platform from https://repo.anaconda.com/miniconda.html
    wget https://repo.anaconda.com/miniconda/Miniconda2-latest-Linux-x86_64.sh -O ~/Miniconda2-latest-Linux-x86_64.sh
    
    # install Python 2, you may install in another location specified by -p
    sh ~/Miniconda2-latest-Linux-x86_64.sh -b -p ~/miniconda2/ 
    
    # this will set up the conda environment for package installation
    source ~/miniconda2/bin/activate
    
    # install the package
    pip install git+https://github.com/SlicerDMRI/whitematteranalysis.git
    
    # define an environment variable so Python 2 can be found by pnlscripts/wmqlqc.py
    export PY2BIN=/absolute/path/to/miniconda2/bin
    
    
[Here](https://github.com/SlicerDMRI/whitematteranalysis) is the detailed instruction for installation. Upon successful 
installation, you should be able to run `~/miniconda2/bin/wm_quality_control_tractography.py --help`.



# Running

*(If you would like, you may edit your [bashrc](#global-bashrc) to have environment automatically setup
every time you open a new terminal)*

## Running individual scripts

### 1. Configure your environment

    source ~/miniconda3/bin/activate           # should introduce '(base)' in front of each line
    conda activate pnlpipe3                    # should introduce '(pnlpipe3)' in front of each line
    export FREESURFER_HOME=~/freesurfer        # you may specify another directory where FreeSurfer is installed
    source $FREESURFER_HOME/SetUpFreeSurfer.sh
    export FSLDIR=~/fsl/                       # setup fsl environment
    source $FSLDIR/etc/fslconf/fsl.sh
    export PATH=$PATH:$FSLDIR/bin
    cd pnlpipe && export PNLPIPE_SOFT=`pwd`/soft_dir

    
### 2. Temporary directory

Both *pnlpipe* and *pnlNipype* have centralized control over various temporary directories created down the pipeline. 
The temporary directories can be large, and may possibly clog the default `/tmp/` directory. You may define custom 
temporary directory with environment variable `PNLPIPE_TMPDIR`:

    mkdir ~/tmp/
    export PNLPIPE_TMPDIR=~/tmp/

    
### 3. Source individual software module

Each software module makes a file called `env.sh` as part of their output,
and sourcing that file will add their software path to the `PATH` environment variable,
as well as set any other necessary environment variables. Currently, the following
modules make an `env.sh` file:

* UKFTractography
* BRAINSTools
* dcm2niix
* ANTs
* tract_querier

E.g. to add `tract_querier` to the `PATH` and `PYTHONPATH`, you would run

    source $PNLPIPE_SOFT/tract_querier-<hash>/env.sh

See [Pipeline scripts overview](#pipeline-scripts-overview) for details about functionality of each script.
See [Shell environment](#2-shell-environment) to learn more about setting up your environment.

Additionally, see [Multiprocessing](#3-multiprocessing) to speed-up your computation.


## Running the pipelines

### 1. Configure your environment

    source ~/miniconda3/bin/activate           # should introduce '(base)' in front of each line
    conda activate pnlpipe3                    # should introduce '(pnlpipe3)' in front of each line
    export FREESURFER_HOME=~/freesurfer        # you may specify another directory where FreeSurfer is installed
    source $FREESURFER_HOME/SetUpFreeSurfer.sh
    export FSLDIR=~/fsl/                       # setup fsl environment
    source $FSLDIR/etc/fslconf/fsl.sh
    export PATH=$PATH:$FSLDIR/bin
    cd pnlpipe && export PNLPIPE_SOFT=`pwd`/soft_dir


### 2. Configure your input data

Edit the paths of `INPUT_KEYS` in `pnlpipe_config.py` to point to your data. See the back-up
`pnlpipe_config.py.example`:

    INPUT_KEYS = {
    'caseid_placeholder': '003_GNX_007',
    'dwi': '/data/pnl/INTRuST/003_GNX_007/raw/003_GNX_007-dwi.nhdr',
    't1': '/data/pnl/INTRuST/003_GNX_007/raw/003_GNX_007-t1w.nhdr',
    't2': '/data/pnl/INTRuST/003_GNX_007/raw/003_GNX_007-t2w.nhdr'
    }

An input path is found by looking up its key (left hand side of colon) in INPUT_KEYS.
Value of each key (right hand side of colon) is returned after substituting a caseid.
So, make sure your input data is organized according to the file structure
you define above. Finally, put the caseids in `./caselist.txt` you want to analyze:

    003_GNX_007
    003_GNX_021
    003_GNX_012
    ...
    ...


### 3. Multiprocessing

Multi-processing is another advanced feature of *pnlpipe*. Scripts like `atlas.py`, `eddy.py`, and `wmql.py` utilizes 
python multi-processing capability to make the work faster. You may specify `NCPU` parameter in `pnlpipe_config.py`.

    NCPU = '8'
    
On a Linux machine, you should find the number of processors by the command `lscpu`:

    On-line CPU(s) list:   0-55 

You can specify any number not greater than the On-line CPU(s). However, one caveat is, other applications in your computer 
may become sluggish or you may run into memory error due to heavier computation in the background. If this is the case, 
reduce NCPU (`--nproc`) to less than 4.

## 3. Analyze data

    ./pnlpipe std run           # runs 'std' pipeline
    ./pnlpipe std status        # reports progress
    ./pnlpipe std summarize     # generates _data/tractmeasures.csv - tract measures for all process cases

See [Run and monitor](#run-and-monitor) and [Listing your pipelines output](#listing-your-pipelines-output) for more details.


# Tests

Two test cases are provided with release >= v2.0.
Download *test_data.zip* from the [release](https://github.com/pnlbwh/pnlpipe/releases) and run test as follows:

    tar -xzvf test_data.zip          # unzip the tar ball
    cd INTRuST                       # you should see cases 003_GNX_007 and 003_GNX_021
    cp pnlpipe_config.py pnlpipe/    # edit pnlpipe_config.py with proper paths
    cp caselist.txt pnlpipe/
    cd pnlpipe/ && ./pnlpipe std run # also ./pnlpipe epi run


# Pipeline scripts overview

`pnlscripts` is a directory of PNL specific scripts that implement various
pipeline steps. The PNL pipelines (via the nodes defined in
`pnlpipe_pipelines/_pnl.py`) call these scripts at each step. These scripts are
the successors to the ones in [pnlutil](https://github.com/pnlbwh/pnlutil).
Besides being more robust and up to date with respect to software such
as [ANTS](http://stnava.github.io/ANTs/), they are implemented in python using
the shell scripting library [plumbum](https://plumbum.readthedocs.io/en/latest/).
Being written in python means they are easier to understand and modify,
and [plumbum](https://plumbum.readthedocs.io/en/latest/) allows them to be
almost as concise as a regular shell script.

You can call any of these scripts directly, e.g.

    ./pnlscripts/bse.py -h

To add them to the path, run `source env.sh`, and you'll be able to call
them from any directory.

It's important to note that usually the scripts are calling other binaries, such
as those in [BRAINSTools](https://github.com/BRAINSia/BRAINSTools/). All the
software they rely on, with the exception of FreeSurfer and FSL, can be
installed by setting up a pipeline and running `./pnlpipe <pipeline> setup`, or
by running `./pnlpipe install <software> `. The software is installed to the
`$PNLPIPE_SOFT` directory. Some of the software modules also write an `env.sh`
file to their output directories, which you can source to add them to your
environment (see the section above). This makes it easy to add them to your
environment before calling any of the scripts in `pnlscripts`.


This table summarizes the scripts in `pnlpipe/pnlscripts/`:

| Category           |  Script                            |  Function                                                             |
|--------------------|------------------------------------|-----------------------------------------------------------------------|
| General            |  **axisAlign.py**                  |   removes oblique coordinate tranform                                 |
| General            |  **center.py**                     |   changes origin to be at the center of the volume                    |
| General            |  **alignAndCenter.py**             |   axis aligns and centers an image                                    |
| General            |  **mask**                          |  skullstrips by applying a labelmap mask                              |
| DWI                |  **antsApplyTransformsDWI.py**     |  applies a transform to a DWI                                         |
| DWI                |  **bse.py**                        |  extracts a baseline b0 image                                         |
| DWI                |  **dwiconvert.py**                 |  DWI conversion                                                       |
| DWI                |  **bet.py**                        |  extracts a baseline b0 image and masks it                            |
| DWI                |  **epi.py**                        |  corrects EPI distortion via registration                             |
| DWI                |  **eddy.py**                       |  corrects eddy distortion via registration                            |
| DWI                |  **dwi_motion_estimate_flirt.py**  |  read transforms by FLIRT and calculates displacement                 |
| Structural         |  **atlas.py**                      |  computes a brain mask from training data                             |
| Structural         |  **fs.py**                         |  runs freesurfer but takes care of some common preprocessing steps    |
| Structural         |  **makeRigidMask.py**              |  rigidly transforms a labelmap to align with another structural image |
| Freesurfer to DWI  |  **fs2dwi.py**                     |  registers a freesurfer segmentation to a DWI                         |
| Tractography       |  **wmql.py**                       |  simple wrapper for tract_querier                                     |
| Tractography       |  **wmqlqc.py**                     |  makes html page of rendered wmql tracts                              |
| Tractography       |  **summarizeTractMeasures.py**     |  makes a summary of tract measures for a project


# DICOM to NRRD

*pnlpipe* accepts 3D/4D MRI in NRRD format. To generate NRRD from DWI, use [dcm2niix](https://github.com/rordenlab/dcm2niix)

    dcm2niix -o outputDir -f namePrefix -z y -e y -b y dicomDir


# Run and monitor

Once you're ready to run the pipeline:

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


# Listing your pipeline's output

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

    ./pnlpipe std ls -s dwied # prints <caseid> for existing paths
    ./pnlpipe std ls -c dwid  # prints <caseid>,<path> for existing paths

You can combine flags together. To get the csv of all missing Freesurfer
subject directories, you would run

    ./pnlpipe std ls -cx fs

The `ls` command helps you inspect your generated data or use it for other types of
processing by piping its results to other commands. Say you want to get the
space directions of all your eddy corrected DWI's, you could do the following:

    ./pnlpipe std ls dwied | unu head | grep 'space directions'



# Setup

*(If you have not configured the following so far, do it now)*

    source ~/miniconda3/bin/activate            # should intoduce '(base)' in front of each line
    conda activate pnlpipe3                     # should introduce '(pnlpipe3)' in front of each line
    export FREESURFER_HOME=~/freesurfer         # you may specify another directory where FreeSurfer is installed
    source $FREESURFER_HOME/SetUpFreeSurfer.sh
    export FSLDIR=~/fsl/                        # setup fsl environment
    source $FSLDIR/etc/fslconf/fsl.sh
    export PATH=$PATH:$FSLDIR/bin
    cd pnlpipe && export PNLPIPE_SOFT=`pwd`/soft_dir

Premade pipelines are in the `pnlpipe_pipelines` directory. For example, the
standard PNL pipeline is defined in `pnlpipe_pipelines/std.py`, and the EPI
correction pipeline is defined in `pnlpipe_pipelines/epi.py`. You can also get a
list of available pipelines by running `./pnlpipe -h`. As an example, we will
run the PNL standard pipeline, the one named `std`.

Before running a pipeline, we need to configure it. This involves two steps:
one, we need to specify its parameters, and two, we need to build the
software it requires.

To specify the parameters, we put them in a [yaml](http://www.yaml.org/start.html)
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
Now build the software by running-

    ./pnlpipe std setup

(if any of the software packages already exist, they will not rebuild). You should now
see the results in `$PNLPIPE_SOFT`, such as `BRAINSTools-bin-2d5eccb/` and
`UKFTractography-421a7ad/`.


# Advanced options

## 1. Parameters

### Multiple Parameter Combinations

Sometimes you'd like to run a pipeline using different parameters, for example
when trying to optimize results, or to test out the effect of different software
versions. The walkthrough briefly mentioned how to have multiple parameter values,
but this section will provide more details.


### Lists of parameter values

Each pipeline has one parameters file: `pnlpipe_params/<pipeline>.params`. This
is a file that is expected to be in [yaml](http://www.yaml.org/start.html)
format and have either a single dictionary, or a list of dictionaries. The keys
of the dictionaries are the names of the arguments to the `make_pipeline`
function in the `pnlpipe_pipelines/<pipeline>.py`, and each key has a list of
values. When this parameter file is read, every combination of parameter values
is calculated, and each of these parameter combinations will be printed when you
run `./pnlpipe <pipeline> status`, and each will be used by pipeline when you
run `./pnlpipe <pipeline> run`.

Here's a simple example.  Say we have a pipeline `pnlpipe_pipelines/simply.py`,
with the following signature for `make_pipeline`:

    def make_pipeline(caseid, inputDwiKey, someparam=0.1):
       ...

When you run `./pnlpipe simple init`, it will make a file like this:

    caseid: [./caselist.txt]
    inputDwiKey: ['*mandatory*']
    someparam: [0.1]

Now say that our `pnlpipe_config.py` looks like the following:

    INPUT_KEYS = {
    'caseid_placeholder': '{case},
    'dwi': '../{case}/{case}-dwi.nhdr',
    'dwiharm': '../{case}/{case}-dwi-harm.nhdr'
    }

where `dwi` stands for our raw DWI's, and `dwiharm` are some preprocessed
versions. To run the `simple` pipeline on both types of DWI using the same
caselist, we would make our parameters

    caseid: [./caselist.txt]
    inputDwiKey: [dwi, dwiharm]
    someparam: [0.1]

Then `./pnlpipe simple status` will show the parameters, output template paths,
and progress for 2 parameter combinations, (`dwi`, `0.1`) and (`dwiharm`, `0.1`).
If we made `someparam: [0.1, 0.2]`, then there would be 4 parameter combinations.

### Lists of parameter dictionaries

Say that for the above example, instead of running the pipeline for `someparam=0.1`
and `someparam=0.2`  for both `dwi` and `dwiharm`, we only wanted to use `0.1` for
`dwi` and `0.2` for `dwiharm`, we could achieve that by writing two separate parameter
dictionaries:

    - caseid: [./caselist.txt]
      inputDwiKey: [dwi]
      someparam: [0.1]


    - caseid: [./caselist.txt]
      inputDwiKey: [dwi]
      someparam: [0.2]

(Make sure that all the parameter names line up with `caseid`!). Another example
is when you have input paths that are in different directories, each having
different case lists. To run the pipeline on both data sets, you would make 2
or more dictionaries:

    - caseid: [./caselist1.txt]
      inputDwiKey: [dwi2]
      someparam: [0.1]


    - caseid: [./caselist2.txt]
      inputDwiKey: [dwi2]
      someparam: [0.1]


### Running and listing specific parameter combinations

`./pnlpipe <pipeline> run` will automatically run for every parameter combination.
To only run it for particular combination, you can use the `-p` switch.

    ./pnlpipe <pipeline> run -p 2

This runs the pipeline for the second parameter combination, as listed by `./pnlpipe <pipeline> status`.
`ls` and `env` behave similarly:

    ./pnlpipe <pipeline> ls dwi -p 1
    eval $(./pnlpipe <pipeline> env -p 1)


## 2. Shell environment

### Pipeline shell environment

Sometimes you want access to the same software environment that your pipeline
does when it runs with a particular parameter combination.  This is possible by using
the `env` command.

    ./pnlpipe <pipeline> env -p 2

prints a Bash setup that exports the software paths and example data paths for
`<pipeline>'s` second parameter combination. To add them to your environment,
run

    eval `./pnlpipe <pipeline> env -p 2`  # or
    eval $(./pnlpipe <pipeline> env -p 2)


### Ad-hoc shell environment

Some of the pre-made software modules make a file called `env.sh` as part of their output,
and sourcing that file will add their software path to the `PATH` environment variable,
as well as set any other necessary environment variables.  Currently, the following
modules make an `env.sh` file:

* UKFTractography
* BRAINSTools
* dcm2niix
* ANTs
* tract_querier
* whitematteranalysis

E.g. to add `tract_querier` to the `PATH` and `PYTHONPATH`, you would run

    source $PNLPIPE_SOFT/tract_querier-<hash>/env.sh
    
Similarly, for ANTs, you would run

    source $PNLPIPE_SOFT/ANTs-bin-<hash>/env.sh


### Global bashrc

If you want your terminal to have the scripts automatically discoverable and environment ready to go,
you may put the following lines in your bashrc:

    source ~/miniconda3/bin/activate            # should intoduce '(base)' in front of each line
    conda activate pnlpipe3                     # should introduce '(pnlpipe3)' in front of each line
    export FREESURFER_HOME=~/freesurfer         # you may specify another directory where FreeSurfer is installed
    source $FREESURFER_HOME/SetUpFreeSurfer.sh
    export FSLDIR=~/fsl                         # you may specify another directory where FreeSurfer is installed
    export PATH=$PATH:$FSLDIR/bin
    source $FSLDIR/etc/fslconf/fsl.sh
    export $PATH=$PATH:/absolute/path/to/pnlpipe/pnlscripts
    export PNLPIPE_SOFT=/absolute/path/to/pnlpipe/soft_dir
    source $PNLPIPE_SOFT/tract_querier-<hash>/env.sh
    source $PNLPIPE_SOFT/BRAINSTools-bin-<hash>/env.sh
    source $PNLPIPE_SOFT/UKFTractography-<hash>/env.sh
    source $PNLPIPE_SOFT/dcm2niix-<hash>/env.sh
    source $PNLPIPE_SOFT/ANTs-bin-<hash>/env.sh


## 3. PNL: Running on the cluster

*(This functionality has not been well tested)*

The PNL uses a high performance computing cluster for most of its data
processing, and this cluster
uses [LSF](https://en.wikipedia.org/wiki/Platform_LSF) to manage batch
processing. *pnlpipe* provides a Makefile that allows you to easily submit your
pipeline jobs to this system.

Edit `Makefile` and replace `std` in the line `PIPE := std` to the name
of the pipeline you wish to run. Now you can submit pipeline jobs for individual
case ids like this:

    make 001-bsub8 002-bsub8 003-bsub8

This submits an 8 core LSF job for each of the case ids `001`, `002`, and `003`.
If resources are limited, 4 cores might be better:

    make 001-bsub4 002-bsub4 003-bsub4

For a large case list, this method is tedious and it's possible that you accidentally submit
a job for a case id that's already in the queue or running.  A better way is to
run

    make caselist-bsub8  # or, make caselist-bsub4

This will iterate over each case id in `caselist.txt` and submit an 8 core job
to the LSF system, but only if that case id is not already running (it uses the
LSF command `bjobs` to determine this). If your caselist is not named
`caselist.txt`, edit the `Makefile` and modify the line `CASELIST :=
caselist.txt` to point to your file.

An alternative to modifying the Makefile is to set the variables on the command
line:

    make PIPE=std CASELIST=caselist2.txt caselist-bsub8


## 4. Installing software without using pipeline

You can install software without configuring a pipeline and running `./pnlpipe <pipeline> setup`.
To do this, use the `install` subcommand:

    ./pnlpipe install <software> [--version <version>]

E.g. to install the `DiffusionPropagator` branch of `UKFTractography`, run

    ./pnlpipe install UKFTractography --version DiffusionPropagator

To install the Github revision `41353e8` of [BRAINSTools](https://github.com/BRAINSia/BRAINSTools/),
run

    ./pnlpipe install BRAINSTools --version 41353e8

Or, to install the master branch:

    ./pnlpipe install BRAINSTools --version master

Each software module interprets version in its own way. Most of the time,
`--version` expects a Github revision, as for these examples. However
the switch is optional; running `install` without specifying a version will
install the software's default version.

Here's an example on how to install the Washington
University's
[HCP Pipeline scripts](https://github.com/Washington-University/Pipelines):

    ./pnlpipe install HCPPipelines --version 3.22.0


## 5. Writing your own pipelines

*(This functionality has not been well tested)*

*pnlpipe* is a well-structured framework for authoring and running file based data
processing pipelines and for automatically installing prerequisite software
packages. Unlike many other data processing software, it allows you to:

* build your pipelines from parameterized nodes that generate their own file paths
* run your pipelines with many parameter combinations without extra work
* write new nodes and pipelines with little boilerplate

It is primarily designed for scientific workflows that have long running
processes and that operate on a set of observations. It comes prepackaged with
some of the [PNL](http://pnl.bwh.harvard.edu)'s neuroimaging pipelines that are
based on a library and scripts that you can use to write new pipelines.

To author a pipeline in *pnlpipe*, you construct a DAG using python code.
This DAG must be returned by a function called `make_pipeline` in
a python module under `pnlpipe_pipelines`.  The name of the module
is used as the name of the pipline.  You will then be able to
run any of the `./pnlpipe <pipeline>` subcommands.

This section will be expanded in the future, but for now, see
`pnlpipe_pipelines/std.py` for an example on how to construct a pipeline, and
see `pnlpipe_pipelines/_pnl.py` for examples on how to write your own nodes.


# Issues

## Known errors

### 1. error setting certificate verify locations

During the setup phase you may encounter this error, in which case
run

    git config --global http.sslverify "false"

and run setup again.


## Support

Create an issue at https://github.com/pnlbwh/pnlpipe/issues . We shall get back to you as early as possible.

