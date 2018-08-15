#!/usr/bin/env python

import sys, io, os, glob, argparse, tempfile
import tarfile
import numpy, numpy as np
import scipy.io

# This code reads a series of transforms written by FLIRT, representing the
# motion-correction of each gradient in a diffusion-weighted MRI image.
# The code then calculates the displacement represented by each transform,
# and saves the result, the mean for each subject, and the case-list to a .mat file.


def load_transforms(path: str):
    """
    Load array of transforms from a directory, or tar/tgz/bz2/zip file containing
    Flirt 4x4 matrices, generally with the filename format 'Diffusion-G#.txt'.
    """

    if (os.path.isfile(path)):
        # Try loading from an archive, if given a single-file path
        archive_reader = tarfile.open(path)
        filenames = archive_reader.getnames()
        filedata = [archive_reader.extractfile(f).read() for f in filenames]
    else:
        # Otherwise, glob the directory
        # FIXME? don't assume the pattern?
        filenames = glob.glob(path + "/Diffusion-*")
        filenames.sort()
        filedata = [open(f, 'rb').read() for f in filenames]
        
    num_grads = len(filenames)

    transforms = np.zeros((num_grads, 4, 4), dtype=np.float64)

    for (i, xfm_txt) in enumerate(filedata):
        xfm = np.genfromtxt(io.BytesIO(xfm_txt))
        assert xfm.shape == (4,4), "Unexpected transform shape {}, expected 4x4 matrix".format(xfm.shape)

        transforms[i] = xfm

    return transforms

def subject_motion(transforms):
    """
    Calculate single-subject motion from (N,4,4) numpy array of transforms.
    """

    # multiply each transform by unit vector (xfm_mat * [1 1 1 1]')
    xfms_disp = np.apply_along_axis(lambda x: np.matmul(x, np.array([1,1,1,1])), 2, transforms)

    # take displacement between subsequent transformed vectors
    xfms_diff = np.diff(xfms_disp, axis=0)

    # store norm of displacements
    xfms_tr = np.zeros(transforms.shape[0])
    for i in range(0,len(transforms) - 1):
        xfms_tr[i+1] = np.linalg.norm(xfms_diff[i])

    return xfms_tr

def motion_estimate(path):
    return subject_motion(load_transforms(path))

def mean_subject_motion(transforms):
    return np.mean(subject_motion(transforms))

def directory_motion_estimate(input_path, output_path=None):
    assert os.path.isdir(input_path), "Expected directory!"

    cases = glob.glob(input_path + '/*')
    cases.sort()

    # run one subject first to get number of gradients
    numgrads = motion_estimate(cases[0]).shape[0]

    # result variables
    #   use `dtype=np.object` to get matlab-equivalent nested arrays in output
    #   note the array nesting below, also for matlab output
    res = np.empty((len(cases),), dtype=np.object)
    motion_estimation = np.zeros(len(cases))

    for i in range(0, len(cases)):
        print("Processing: {}".format(cases[i]))
        res[i] = np.array([motion_estimate(cases[i])])
        motion_estimation[i] = np.mean(res[i])

    mat_data = {'cases': cases,
                'res': res,
                'motion_estimation': motion_estimation}

    if output_path is not None:
        scipy.io.savemat(output_path, mat_data)

    return mat_data

def _test(testdata_dir):
    """
    - Load datasets from `testdata_dir`, assumed to contain the following files:
        - {test1,test2,test3}-dwi-B3000-Ed-xfms.tgz
            
            Each archive holds a set of txt files with the naming convention
            `Diffusion-G##.txt`, and containing 4x4 transforms.
        - {test1,test2,test3}-motionEstimate_general_2.mat

            Reference results from running the original matlab code.

    - Runs the motion calculation directly on the tgz files, and on temp
      temp directory where the files have been extracted.
    - Compares results to the reference .mat files.
    """

    # test individual subjects
    subjects = ['test1', 'test2', 'test3']
    for s in subjects:
        data_basename = os.path.join(testdata_dir, s+'-dwi-B3000-Ed-xfms')
        mtn = subject_motion(load_transforms(data_basename))

        # load the result saved from matlab
        mtn_mat = scipy.io.loadmat(data_basename+'.motionEstimate_general_2.mat')[s].flatten()

        # expand and load from temp directory
        tmpdir = tempfile.mkdtemp()
        tarfile.open(data_basename + '.tgz').extractall(tmpdir)
        mtn_dir = subject_motion(load_transforms(tmpdir))

        # our calculation should be equal for either path
        np.testing.assert_array_equal(mtn, mtn_dir)

        # assert equal up to tolerance compared to matlab output
        np.testing.assert_allclose(mtn, mtn_mat, rtol=1e-15)
        np.testing.assert_allclose(mtn_dir, mtn_mat, rtol=1e-15)
    print("All tests passed.")

    

def main(args=sys.argv):
    # handle arguments
    parser = argparse.ArgumentParser('Process args')
    group = parser.add_mutually_exclusive_group()

    group.add_argument('--single_subject', '-s',
                        help="Calculate motion for a single subject (directory or tgz file), save \
                        result to specified .mat file.",
                        action='store_true', required=False)

    group.add_argument('--test',
                        help="Run tests. 'datapath' should be test data directory."
                        action='store_true', required=False)

    parser.add_argument('datapath',
                        help="Input data: directory or archive",
                        type=str)
    parser.add_argument('output',
                        help="Output (.mat) file",
                        type=str)

    args = parser.parse_args(sys.argv[1:])

    if args.test:
        _test(args.datapath) # this will exit on throw
        sys.exit(0)

    elif args.single_subject:
        if (not os.path.exists(os.path.dirname(args.single_subject)) or
            os.path.isdir(args.single_subject_)):
            print("Error: --single_subject argument must be filename, in an existing directory")
            sys.exit(1)

        res = subject_motion(load_transforms(args.datapath))
        scipy.io.savemat(args.single_subject, {'res': res})
        print("Saved variable 'res' in file: {}".format(args.single_subject))
        sys.exit(0)

    else:
        directory_motion_estimate(args.datapath, output_path=args.output)
        sys.exit(0)


if __name__ == '__main__':
    main()
