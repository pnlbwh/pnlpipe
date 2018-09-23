#!/usr/bin/env python
#
# How does this compare to `unu unorient`?

import sys
import os
from os.path import basename, splitext, abspath, exists
import argparse
import tempfile
from subprocess import Popen, PIPE
import re
import numpy
from numpy import matrix, identity, diag
from numpy import linalg
from numpy.linalg import inv
from numpy.testing import assert_almost_equal
import fileinput
from subprocess import check_call

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

def t(cmd):
    """
    >>> t(['ls', '-a', '>', '/dev/null'])
    ls -a > /dev/null
    >>> t('ls -a > /dev/null')
    ls -a > /dev/null
    """

    if isinstance(cmd, list):
        cmd = ' '.join(cmd)

    print("* " + cmd)
    check_call(cmd, shell=True)

def replace_line_in_file(afile, match_string, replace_with):
    for line in fileinput.FileInput(afile, inplace=1):
        if match_string in line:
            line = replace_with
        print(line)

def find_spc_dir(s):
    match = re.search(
  'space directions: \((?P<xvec>(.*))\) \((?P<yvec>(.*))\) \((?P<zvec>(.*))\)',
        s)
    xvec = [float(x) for x in match.group('xvec').split(',')]
    yvec = [float(x) for x in match.group('yvec').split(',')]
    zvec = [float(x) for x in match.group('zvec').split(',')]
    return [xvec, yvec, zvec]


def find_mf(s):
    match = re.search(
 'measurement frame: \((?P<xvec>(.*))\) \((?P<yvec>(.*))\) \((?P<zvec>(.*))\)',
        s)
    xvec = [float(x) for x in match.group('xvec').split(',')]
    yvec = [float(x) for x in match.group('yvec').split(',')]
    zvec = [float(x) for x in match.group('zvec').split(',')]
    return [xvec, yvec, zvec]


def get_hdr(nrrd):
    hdr, stderr = Popen(['unu', 'head', nrrd], stdout=PIPE,
                           stderr=PIPE).communicate()
    return hdr


@pushd(tempfile.mkdtemp())


def get_numpy_rotation(spcdir_orig):
    sizes = diag([linalg.norm(spcdir_orig[0,:]),linalg.norm(spcdir_orig[1,:]),linalg.norm(spcdir_orig[2,:])])
    spcON = linalg.inv(sizes) * spcdir_orig
    spcNN = numpy.zeros([3,3])
    for i in range(0,3):
        mi = numpy.argmax(abs(spcON[i,:]))
        spcNN[i,mi] = numpy.sign(spcON[i,mi])
    R = spcNN * spcON.I
    return R


def axis_align_dwi(dwi, outfile=None, precision=5):
    dwi_hdr = get_hdr(dwi)
    spcdir_orig = matrix(find_spc_dir(dwi_hdr))
    print(spcdir_orig)
    sizes = diag([linalg.norm(spcdir_orig[0,:]),linalg.norm(spcdir_orig[1,:]),linalg.norm(spcdir_orig[2,:])])
    print(sizes)
    R = get_numpy_rotation(spcdir_orig)
    print(R)
    spcdir_new = matrix.round(sizes *R*linalg.inv(sizes)*spcdir_orig,4)
    print(spcdir_new)

    mf_orig = find_mf(dwi_hdr)
    print(mf_orig)
    mf_new = matrix.round(R * matrix(mf_orig),4)
    print(mf_new)
    mf_new = [','.join(map(str, x)) for x in mf_new.tolist()]
    newline = 'measurement frame: (%s) (%s) (%s)\n' % (mf_new[0], mf_new[1],
                                                     mf_new[2])
    dwi_new = splitext(dwi)[0] + '_axisaligned.nhdr' if not outfile else \
            outfile
    t('unu save -f nrrd -e gzip -i "%s" -o "%s"' % (dwi, dwi_new))
    replace_line_in_file(dwi_new, 'measurement frame:', newline)

    newline = 'space directions: (%s) (%s) (%s) none\n' % (','.join(map(str, spcdir_new[0])),
                                                           ','.join(map(str, spcdir_new[1])),
                                                           ','.join(map(str, spcdir_new[2])))
    replace_line_in_file(dwi_new, 'space directions:', newline)


# Why not just ConvertBetweenFileFormats??
def axis_align_3d(image, outfile=None):
    img_hdr = get_hdr(image)
    spcdir_orig = matrix(find_spc_dir(img_hdr))
    print(spcdir_orig)
    sizes = diag([linalg.norm(spcdir_orig[0,:]),linalg.norm(spcdir_orig[1,:]),linalg.norm(spcdir_orig[2,:])])
    print(sizes)
    R = get_numpy_rotation(spcdir_orig)
    print(R)
    spcdir_new = matrix.round(sizes *R*linalg.inv(sizes)*spcdir_orig,4)
    print(spcdir_new)

    image_new = splitext(image)[0] + '_axisaligned.nhdr' if not outfile else \
            outfile
    t('unu save -f nrrd -e gzip -i "%s" -o "%s"' % (image, image_new))
    newline = 'space directions: (%s) (%s) (%s)\n' % (','.join(map(str, spcdir_new[0])),
                                                      ','.join(map(str, spcdir_new[1])),
                                                      ','.join(map(str, spcdir_new[2])))
    replace_line_in_file(image_new, 'space directions:', newline)


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument('-i','--infile', help='a 3d or 4d nrrd image')
    argparser.add_argument('-o','--outfile', help='a 3d or 4d nrrd image',
                          required=False)
    argparser.add_argument('-p','--precision',
                           help='precision of computed rotation matrix for dwi gradients',
                          required=False, type=int, default=5)
    argparser.add_argument('--force', action='store_true', default=False,
                           help='overwrite outfile if it exists')
    args = argparser.parse_args()

    image_in = abspath(args.infile)

    if not exists(image_in):
        print(image_in + ' doesn\'t exist')
        return

    if exists(args.outfile) and not args.force:
        print(args.outfile + ' already exists.')
        print('Delete it first.')
        sys.exit(1)

    match = re.search('dimension: (?P<dimension>\d)', get_hdr(image_in))
    dim = match.group('dimension')

    if dim == '4':
        axis_align_dwi(image_in, outfile=args.outfile,
                       precision=args.precision)
    elif dim == '3':
        axis_align_3d(image_in, outfile=args.outfile)
    else:
        print(image_in + ' has dimension %s, needs to be 3 or 4' % dim)


if __name__ == '__main__':
    main()
