#!/usr/bin/env python

from __future__ import print_function
import operator
from util import logfmt, ExistingNrrdOrNifti, Nrrd
from plumbum import local, cli, FG
from plumbum.cmd import unu, ImageMath

import logging
logger = logging.getLogger()
logging.basicConfig(level=logging.DEBUG, format=logfmt(__file__))


def isNifti(f):
    return '.nii' in f.suffixes


def isNrrd(f):
    return '.nrrd' in f.suffixes or '.nhdr' in f.suffixes


def get_grad_dirs(hdr):
    return [map(float, line.split('=')[1].split())
            for line in hdr.splitlines() if 'DWMRI_gradient' in line]


def get_bval(hdr):
    for line in hdr.splitlines():
        if 'b-value' in line:
            return float(line.split('=')[1])


def nrrd_get_b0_index(dwi):
    dwi = local.path(dwi)
    hdr = unu("head", dwi)[:-1]
    def norm(vector):
        return sum([v**2 for v in vector])
    bval = get_bval(hdr)
    bvals = [norm(gdir) * bval for gdir in get_grad_dirs(hdr)]
    idx, min_bval = min(enumerate(bvals), key=operator.itemgetter(1))
    logger.info("Found B0 of " + str(min_bval) + " at index " + str(idx))
    return idx


def fsl_get_b0_index(dwi):
    with open(dwi.with_suffix('.bval', depth=2) ,'r') as f:
        bvals = map(int, f.read().split())
    return [bval < 45 for bval in bvals].index(True)


def fsl_extract_b0(dwi, output):
    dwi = local.path(dwi)
    idx = fsl_get_b0_index(dwi)
    from plumbum.cmd import fslroi
    fslroi(dwi, output, idx, 1)


def nrrd_extract_b0(dwi, out):
    idx = nrrd_get_b0_index(dwi)
    slicecmd = unu["slice", "-a", "3", "-p", str(idx), "-i", dwi]
    gzipcmd = unu["save", "-e", "gzip", "-f", "nrrd", "-o", out]
    (slicecmd | gzipcmd) & FG


class App(cli.Application):
    """Extracts the baseline (b0) from a nrrd or nifti DWI.  Assumes
the diffusion volumes are indexed by the last axis."""

    dwimask = cli.SwitchAttr(
        ['-m', '--mask'], ExistingNrrdOrNifti, help='DWI mask', mandatory=False)
    dwi = cli.SwitchAttr(
        ['-i', '--infile'], ExistingNrrdOrNifti, help='DWI', mandatory=True)
    out = cli.SwitchAttr(
        ['-o', '--out'], Nrrd, help='Extracted B0 image', mandatory=True)

    def main(self):
        if isNifti(self.dwi):
            fsl_extract_b0(self.dwi, self.out)
        elif isNrrd(self.dwi):
            nrrd_extract_b0(self.dwi, self.out)
        else:
            raise Exception("Invalid dwi format, must be nrrd or nifti")

        if self.dwimask:
            from plumbum.cmd import ImageMath
            ImageMath(3, self.out, 'm', self.out, self.dwimask)


if __name__ == '__main__':
    App.run()
