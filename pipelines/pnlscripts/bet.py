#!/usr/bin/env python
from util.scripts import bse_py
from plumbum.cmd import bet, ConvertBetweenFileFormats
from plumbum import cli, FG
from util import Nrrd, ExistingNrrd, TemporaryDirectory
import logging

class App(cli.Application):
    force = cli.Flag(['--force'], help='Force overwrite if output already exists',mandatory=False,default=False)
    threshold = cli.SwitchAttr('-f', help='Bet fractional intensity threshold', default=0.1)
    dwi = cli.SwitchAttr(
        ['-i', '--input'],
        ExistingNrrd,
        help='Input DWI',
        mandatory=True)
    out = cli.SwitchAttr(
        ['-o', '--out'], Nrrd,
        help='output DWI mask',
        mandatory=True)

    def main(self):
        if self.out.exists() and not self.force:
            logging.error("'{}' already exists, use --force to force overwrite")
            import sys
            sys.exit(1)
        with TemporaryDirectory() as tmpdir:
            #nii = tmpdir / 'dwi.nii.gz'
            bse = tmpdir / 'bse.nrrd'
            bsenii = tmpdir / 'bse.nii.gz'
            bse_py['-i', self.dwi, '-o', bse] & FG
            ConvertBetweenFileFormats[bse, bsenii] & FG
            #convertdwi_py['-i', self.dwi, '-o', nii] & FG
            bet[bsenii, tmpdir / 'dwi', '-m', '-f', self.threshold] & FG
            ConvertBetweenFileFormats[tmpdir / 'dwi_mask.nii.gz', self.out] & FG

if __name__ == '__main__':
    App.run()
