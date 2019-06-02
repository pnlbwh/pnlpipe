#!/usr/bin/env python
from util.scripts import bse_py
from plumbum.cmd import bet, ConvertBetweenFileFormats
from plumbum import cli, FG
from util import Nrrd, ExistingNrrd, ExistingNrrdOrNifti, TemporaryDirectory
from util.scripts import bse_py

import logging, sys

def nifti(f):
    return '.nii' in f.suffixes
def nrrd(f):
    return '.nrrd' in f.suffixes or '.nhdr' in f.suffixes


class App(cli.Application):
    '''Extracts a baseline b0 image and masks it'''

    force = cli.Flag(['--force'], help='Force overwrite if output already exists',mandatory=False,default=False)
    threshold = cli.SwitchAttr('-f', help='Bet fractional intensity threshold', default=0.1)
    dwi = cli.SwitchAttr(
        ['-i', '--input'],
        ExistingNrrdOrNifti,
        help='Input DWI',
        mandatory=True)
    out = cli.SwitchAttr(
        ['-o', '--out'], Nrrd,
        help='output DWI mask',
        mandatory=True)

    def main(self):
        if self.out.exists() and not self.force:
            logging.error("'{}' already exists, use --force to force overwrite")
            sys.exit(1)
        with TemporaryDirectory() as tmpdir:

            if nrrd(self.dwi):
                bse = tmpdir / 'bse.nrrd'
                bse_py['-i', self.dwi, '-o', bse] & FG
                bsenii = tmpdir / 'bse.nii.gz'
                ConvertBetweenFileFormats[bse, bsenii] & FG
                bet[bsenii, tmpdir / 'dwi', '-m', '-f', self.threshold] & FG
            else:
                # nifti
                # FSL 6.0.1, unlike <=5.0.11, doesn't create only one mask corresponding to b0 extracted from given DWI
                # hence we need to provide baseline image to bet like we did for nrrd above
                bsenii = tmpdir / 'bse.nii.gz'
                bse_py['-i', self.dwi, '-o', bsenii] & FG
                bet[bsenii, tmpdir / 'dwi', '-m', '-f', self.threshold] & FG

            ConvertBetweenFileFormats[tmpdir / 'dwi_mask.nii.gz', self.out] & FG

if __name__ == '__main__':
    App.run()
