#!/usr/bin/env python
from __future__ import print_function
from util import logfmt, TemporaryDirectory
from plumbum import local, cli, FG
import sys, psutil
from util.scripts import bse_py, antsRegistrationSyNMI_sh
from util.antspath import ResampleImageBySpacing, antsApplyTransforms
import os

import logging
logger = logging.getLogger()
logging.basicConfig(level=logging.DEBUG, format=logfmt(__file__))

N_CPU= str(psutil.cpu_count())

class FsToDwi(cli.Application):
    """Registers Freesurfer labelmap to DWI space."""

    fsdir = cli.SwitchAttr(
        ['-f', '--freesurfer'],
        cli.ExistingDirectory,
        help='freesurfer subject directory',
        mandatory=True)
    dwi = cli.SwitchAttr(
        ['-t', '--target'],
        cli.ExistingFile,
        help='target DWI',
        mandatory=True)
    dwimask = cli.SwitchAttr(
        ['-m', '--mask'], cli.ExistingFile, help='DWI mask', mandatory=True)
    out = cli.SwitchAttr(
        ['-o', '--out'],
        cli.NonexistentPath,
        help='output directory',
        mandatory=True)

    def main(self, *args):
        if args:
            print("Unknown command {0!r}".format(args[0]))
            return 1
        if not self.nested_command:
            print("No command given")
            return 1  # error exit code


@FsToDwi.subcommand("direct")
class Direct(cli.Application):
    """Direct registration from Freesurfer to B0."""

    def main(self):
        fshome = local.path(os.getenv('FREESURFER_HOME'))
        if not fshome:
            logging.error('Set FREESURFER_HOME first.')
            sys.exit(1)

        with TemporaryDirectory() as tmpdir:
            tmpdir = local.path(tmpdir)
            b0masked = tmpdir / "b0masked.nrrd"
            b0masked1mm = tmpdir / "b0masked1mm.nrrd"
            brain = tmpdir / "brain.nii.gz"
            wmparc = tmpdir / "wmparc.nii.gz"
            brainmgz = self.parent.fsdir / 'mri/brain.mgz'
            wmparcmgz = self.parent.fsdir / 'mri/wmparc.mgz'
            wmparcindwi1mm = tmpdir / 'wmparcInDwi1mm.nii.gz'

            logging.info(
                "Make brain.nii.gz and wmparc.nii.gz from their mgz versions")
            vol2vol = local[fshome / 'bin/mri_vol2vol']
            label2vol = local[fshome / 'bin/mri_label2vol']
            with local.env(SUBJECTS_DIR=''):
                vol2vol('--mov', brainmgz, '--targ', brainmgz, '--regheader',
                        '--o', brain)
                label2vol('--seg', wmparcmgz, '--temp', brainmgz,
                          '--regheader', wmparcmgz, '--o', wmparc)

            logging.info('Extract B0 from DWI and mask')
            bse_py('-i', self.parent.dwi, '-m', self.parent.dwimask, '-o', b0masked)
            logging.info('Made masked B0')

            logging.info('Upsample masked baseline to 1x1x1')
            ResampleImageBySpacing('3', b0masked, b0masked1mm, '1', '1', '1')
            logging.info('Made 1x1x1 baseline')

            logging.info('Register wmparc to B0')
            pre = tmpdir / 'fsbrain_to_b0'
            affine = pre + '0GenericAffine.mat'
            warp = pre + '1Warp.nii.gz'
            antsRegistrationSyNMI_sh['-m', brain, '-f', b0masked1mm, '-o', pre,
                                     '-n', N_CPU] & FG
            antsApplyTransforms('-d', '3', '-i', wmparc, '-t', warp, affine,
                                '-r', b0masked1mm, '-o', wmparcindwi1mm,
                                '--interpolation', 'NearestNeighbor')
            logging.info('Made ' + wmparcindwi1mm)

            logging.info('Make output directory')
            self.parent.out.mkdir()
            b0masked.copy(self.parent.out)
            b0masked1mm.copy(self.parent.out)
            wmparcindwi1mm.copy(self.parent.out)
            # TODO add dwi resolution wmparcindwi


@FsToDwi.subcommand("witht2")
class WithT2(cli.Application):
    """Registration from Freesurfer to T1 to T2 to B0."""

    def main(self):
        print('TODO')


if __name__ == '__main__':
    FsToDwi.run()
