#!/usr/bin/env python

import sys
import os
from os.path import splitext, abspath, exists
import argparse
import tempfile
import numpy
from numpy import matrix, diag, array, linalg
from numpy import linalg
import nrrd

def pushd(tmpdir):
    """
    Change the working directory of the decorated function.

    Makes the decorated function's code cleaner.
    """
    def wrap(f):
        def new_function(*args, **kw):
            orig_dir = os.getcwd()
            print('* Changing to working dir %s' % tmpdir)
            os.chdir(tmpdir)
            output = f(*args, **kw)
            os.chdir(orig_dir)
            return output
        return new_function
    return wrap

def get_attr(filename):
    img= nrrd.read(filename)

    mri= img[0]
    hdr= img[1]

    return (mri, hdr)


@pushd(tempfile.mkdtemp())


def get_numpy_rotation(spcdir_orig):

    sizes = diag([linalg.norm(spcdir_orig[0,:]),linalg.norm(spcdir_orig[1,:]),linalg.norm(spcdir_orig[2,:])])
    spcON = linalg.inv(sizes) @ spcdir_orig
    spcNN = numpy.zeros([3,3])

    for i in range(0,3):
        mi = numpy.argmax(abs(spcON[i,:]))
        spcNN[i,mi] = numpy.sign(spcON[i,mi])

    R = spcNN @ linalg.inv(spcON)

    return R


def axis_align_dwi(dwi, hdr_out, outfile=None, precision=5):

    # hdr_out= hdr.copy()

    spcdir_orig= hdr_out['space directions'][0:3, 0:3]
    print(spcdir_orig)

    sizes = diag([linalg.norm(spcdir_orig[0,:]),linalg.norm(spcdir_orig[1,:]),linalg.norm(spcdir_orig[2,:])])
    print(sizes)

    R = get_numpy_rotation(spcdir_orig)
    print(R)

    spcdir_new = matrix.round(sizes @ R @ linalg.inv(sizes) @ spcdir_orig, precision)
    print(spcdir_new)

    mf_orig= hdr_out['measurement frame']
    print(mf_orig)

    mf_new = matrix.round(R @ matrix(mf_orig), precision)
    print(mf_new)

    hdr_out['space directions'][0:3, 0:3]= array(spcdir_new)
    hdr_out['measurement frame'] = array(mf_new)

    nrrd.write(outfile, dwi, header=hdr_out, compression_level = 1)


def axis_align_3d(mri, hdr_out, outfile=None, precision= 5):

    # hdr_out= hdr.copy()

    spcdir_orig = hdr_out['space directions'][0:3, 0:3]
    print(spcdir_orig)

    sizes = diag([linalg.norm(spcdir_orig[0,:]),linalg.norm(spcdir_orig[1,:]),linalg.norm(spcdir_orig[2,:])])
    print(sizes)

    R = get_numpy_rotation(spcdir_orig)
    print(R)

    spcdir_new = matrix.round(sizes @ R @ linalg.inv(sizes) @ spcdir_orig, precision)
    print(spcdir_new)

    hdr_out['space directions'][0:3, 0:3]= array(spcdir_new)

    nrrd.write(outfile, mri, header=hdr_out, compression_level = 1)


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument('-i','--infile', help='a 3d or 4d nrrd image', required= True)
    argparser.add_argument('-o','--outfile', help='a 3d or 4d nrrd image', required= True)
    argparser.add_argument('-p','--precision',
                           help='precision of computed rotation matrix for dwi gradients',
                           required=False, type=int, default=5)
    argparser.add_argument('--force', action='store_true', default=False,
                           help='overwrite outfile if it exists')
    args = argparser.parse_args()

    image_in = abspath(args.infile)
    image_new = abspath(args.outfile)

    if not exists(image_in):
        print(image_in + ' doesn\'t exist')
        return

    if exists(args.outfile) and not args.force:
        print(args.outfile + ' already exists.')
        print('Delete it first.')
        sys.exit(1)

    mri, hdr= get_attr(image_in)
    dim= str(hdr['dimension'])


    hdr_out= hdr.copy()

    if 'data file' in hdr_out.keys():
        del hdr_out['data file']
    elif 'datafile' in hdr_out.keys():
        del hdr_out['datafile']

    if 'content' in hdr_out.keys():
        del hdr_out['content']


    if dim == '4':
        axis_align_dwi(mri, hdr_out, outfile= image_new, precision= args.precision)
    elif dim == '3':
        axis_align_3d(mri, hdr_out, outfile= image_new, precision= args.precision)
    else:
        print(image_in + ' has dimension %s, needs to be 3 or 4' % dim)


if __name__ == '__main__':
    main()
