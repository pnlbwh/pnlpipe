#!/usr/bin/env python
from __future__ import print_function
from util import logfmt, TemporaryDirectory
import util
from plumbum import local, cli, FG
from plumbum.cmd import ConvertBetweenFileFormats, ImageMath
from itertools import zip_longest
import pandas as pd
import sys
import os


import logging
logger = logging.getLogger()
logging.basicConfig(level=logging.DEBUG, format=logfmt(__file__))


class App(cli.Application):
    """Convenient script to run freesurfer."""

    t1 = cli.SwitchAttr(
        ['-i', '--input'],
        cli.ExistingFile,
        help='t1 image in nifti or nrrd format (nrrd, nhdr, nii, nii.gz)',
        mandatory=True)
    t1mask = cli.SwitchAttr(
        ['-m', '--mask'],
        cli.ExistingFile,
        help='mask the t1 before running Freesurfer',
        mandatory=False)
    # excludes=['--skullstrip', '-s'])
    # skullstrip = cli.Flag(
    #     ['-s', '--skullstrip'],
    #     excludes=['-m', '--mask'],
    #     help='tells Freesurfer to skullstrip the t1')
    force = cli.Flag(
        ['-f', '--force'],
        help='force a re-run if output folder already exists')
    out = cli.SwitchAttr(
        ['-o', '--out'],
        help='output directory (e.g. <case>-freesurfer)',
        mandatory=True)

    def main(self):
        fshome = local.path(os.getenv('FREESURFER_HOME'))

        if not fshome:
            logging.error('Set FREESURFER_HOME first.')
            sys.exit(1)

        if not self.force and os.path.exists(self.out):
            logging.error(
                'Output directory exists, use -f/--force to force an overwrite.')
            sys.exit(1)

        with TemporaryDirectory() as tmpdir, local.env(SUBJECTS_DIR=tmpdir, FSFAST_HOME='', MNI_DIR=''):

            if self.t1mask:
                logging.info('Mask the t1')
                ImageMath('3', tmpdir / 't1masked.nii.gz', 'm', self.t1, self.t1mask)
                t1 = tmpdir / 't1masked.nii.gz'
                skullstrip = '-noskullstrip'
            else:
                skullstrip = ''
                if '.nrrd' in self.t1.suffixes or '.nhdr' in self.t1.suffixes:
                    logging.info('t1 is in nrrd format, convert to nifti')
                    t1 = tmpdir / 't1.nii.gz'
                    ConvertBetweenFileFormats(self.t1, t1)

            logging.info("Run freesurfer on " + t1)
            subjid = t1.stem

            from plumbum.cmd import bash
            bash['-c', 'recon-all -s '+subjid+' -i '+t1+' -autorecon1 ' +skullstrip] & FG
            (tmpdir / subjid / 'mri/T1.mgz').copy(tmpdir / subjid / 'mri/brainmask.mgz')
            bash['-c', 'recon-all -autorecon2 -subjid '+subjid] & FG
            bash['-c', 'recon-all -autorecon3 -subjid '+subjid] & FG
            logging.info("Freesurfer done.")

            (tmpdir / subjid).copy(self.out, override=True)  # overwrites existing
            logging.info("Made " + self.out)


if __name__ == '__main__':
    App.run()
