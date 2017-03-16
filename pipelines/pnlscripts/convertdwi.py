#!/usr/bin/env python
from __future__ import print_function
import sys
from util import logfmt, ExistingNrrdOrNifti, TemporaryDirectory
from plumbum import cli, FG, local
from plumbum.cmd import unu, DWIConvert, ConvertBetweenFileFormats

import logging
logger = logging.getLogger()
logging.basicConfig(level=logging.DEBUG, format=logfmt(__file__))


def nifti(f):
    return '.nii' in f.suffixes
def nrrd(f):
    return '.nrrd' in f.suffixes or '.nhdr' in f.suffixes
def bval(f):
    return f.with_suffix('.bval', depth=2)
def bvec(f):
    return f.with_suffix('.bvec', depth=2)


class App(cli.Application):
    """Converts between DWI formats using unu, DWIConvert and ConvertBetweenFileFormats"""

    force = cli.Flag(['-f','--force'], help='Force overwrite if output already exists',mandatory=False,default=False)
    dwi = cli.SwitchAttr(
        ['-i', '--input'],
        ExistingNrrdOrNifti,
        help='Input DWI (nrrd or nifti)',
        mandatory=True)
    out = cli.SwitchAttr(
        ['-o', '--out'],
        help='output DWI (nrrd or nifti)',
        mandatory=True)

    def main(self):
        dwi = self.dwi
        out = local.path(self.out)

        if self.force and out.exists():
            out.delete()

        if dwi.suffixes == out.suffixes:
            dwi.copy(out)
        elif nrrd(dwi) and nrrd(out):
            unu('save', '-e', 'gzip', '-f', 'nrrd', '-i', dwi, '-o', out)
        elif nrrd(dwi) and nifti(out):
            DWIConvert('--conversionMode', 'NrrdToFSL', '--inputVolume', dwi,
                       '-o', out)
        elif nifti(dwi) and nrrd(out):
            with TemporaryDirectory() as t:
                t = local.path(t)
                ConvertBetweenFileFormats(dwi, t / 'short.nii.gz', 'short')
                DWIConvert('--conversionMode', 'FSLToNrrd', '--inputBValues',
                           bval(dwi), '--inputBVectors', bvec(dwi),
                           '--inputVolume', t / 'short.nii.gz', '-o', out)
            #(unu['permute', '-p','1','2','3','0', '-i', out] | \
                #unu['save', '-e', 'gzip', '-f', 'nrrd', '-o', out]) & FG
            (unu['save', '-e', 'gzip', '-f', 'nrrd', '-i', out, '-o', out]) & FG
        elif nifti(dwi) and nifti(out):
            ConvertBetweenFileFormats(dwi, out)
        else:
            logging.error('Dwi\'s must be nrrd or nifti.')
            sys.exit(1)


if __name__ == '__main__':
    App.run()
