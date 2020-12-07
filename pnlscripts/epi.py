#!/usr/bin/env python
from __future__ import print_function
from os import getpid
from util import logfmt, TemporaryDirectory, ExistingNrrd, NonexistentNrrd, Nrrd
from util.scripts import bse_py, antsApplyTransformsDWI_py
from util.antspath import antsRegistrationSyN_sh, antsApplyTransforms, antsRegistration
from plumbum import local, cli, FG
from plumbum.cmd import unu
import sys

import logging
logger = logging.getLogger()
logging.basicConfig(level=logging.DEBUG, format=logfmt(__file__))


class App(cli.Application):

    debug = cli.Flag(
        ['-d', '--debug'], help='Debug, save intermediate files in \'epidebug-<pid>\'')
    force = cli.Flag(
        ['-f', '--force'], help='Force overwrite if output already exists')
    dwi = cli.SwitchAttr('--dwi', ExistingNrrd, help='DWI', mandatory=True)
    dwimask = cli.SwitchAttr( '--dwimask', ExistingNrrd, help='DWI mask', mandatory=True)
    t2 = cli.SwitchAttr('--t2', ExistingNrrd, help='T2w', mandatory=True)
    t2mask = cli.SwitchAttr( '--t2mask', ExistingNrrd, help='T2w mask', mandatory=True)
    out = cli.SwitchAttr( ['-o', '--out'], Nrrd, help='EPI corrected DWI, prefix is used for saving mask', mandatory=True)
    typeCast = cli.Flag(
        ['-c', '--typeCast'], help='convert the output to int16 for UKFTractography')

    nproc = cli.SwitchAttr(
        ['-n', '--nproc'], help='''number of threads to use, if other processes in your computer 
        becomes sluggish/you run into memory error, reduce --nproc''', default= 8)

    def main(self):
        if not self.force and self.out.exists():
            logging.error("'{}' already exists, use '--force' to force overwrite.".format(self.out))
            sys.exit(1)
        with TemporaryDirectory() as tmpdir:
            tmpdir = local.path(tmpdir)
            bse = tmpdir / "maskedbse.nrrd"
            t2masked = tmpdir / "maskedt2.nrrd"
            t2inbse = tmpdir / "t2inbse.nrrd"
            epiwarp = tmpdir / "epiwarp.nii.gz"

            t2tobse_rigid = tmpdir / "t2tobse_rigid"
            affine = tmpdir / "t2tobse_rigid0GenericAffine.mat"


            logging.info('1. Extract and mask the DWI b0')
            bse_py('-m', self.dwimask, '-i', self.dwi, '-o', bse)

            logging.info("2. Mask the T2")
            unu("3op", "ifelse", self.t2mask, self.t2, "0", "-o", t2masked)

            logging.info(
                "3. Compute a rigid registration from the T2 to the DWI baseline")
            antsRegistrationSyN_sh("-d", "3", "-f", bse, "-m", t2masked, "-t",
                                   "r", "-o", tmpdir / "t2tobse_rigid")

            antsApplyTransforms("-d", "3", "-i", t2masked, "-o", t2inbse, "-r",
                                bse, "-t", affine)

            logging.info(
                "4. Compute 1d nonlinear registration from the DWI to the T2 along the phase direction")
            moving = bse
            fixed = t2inbse
            pre = tmpdir / "epi"
            dwiepi = tmpdir / ("dwiepi" + ''.join(self.out.suffixes))
            antsRegistration("-d", "3", "-m",
                             "cc[" + str(fixed) + "," + str(moving) + ",1,2]", "-t",
                             "SyN[0.25,3,0]", "-c", "50x50x10", "-f", "4x2x1",
                             "-s", "2x1x0", "--restrict-deformation", "0x1x0",
                             "-v", "1", "-o", pre)

            local.path(str(pre) + "0Warp.nii.gz").move(epiwarp)

            logging.info("5. Apply warp to the DWI")
            antsApplyTransformsDWI_py['-i', self.dwi, '-m', self.dwimask, '-t', epiwarp, '-o', dwiepi,
                                      '-n', str(self.nproc)] & FG
            

            logging.info('6. Apply warp to the DWI mask')
            epimask = self.out.dirname / self.out.basename.split('.')[0]+ '-mask.nrrd'
            antsApplyTransforms('-d', '3', '-i', self.dwimask, '-o', epimask,
                                '-n', 'NearestNeighbor', '-r', bse, '-t', epiwarp)
            unu('convert', '-t', 'uchar', '-i', epimask, '-o', epimask)

            if '.nhdr' in dwiepi.suffixes:
                unu("save", "-e", "gzip", "-f", "nrrd", "-i", dwiepi, "-o", self.out)
            else:
                dwiepi.move(self.out)

            # FIXME: the following conversion is only for UKFTractography, should be removed in future
            if self.typeCast:
                unu('convert', '-t', 'int16', '-i', self.out, '-o', self.out)

            if self.debug:
                tmpdir.copy(self.out.dirname / ("epidebug-" + str(getpid())))


if __name__ == '__main__':
    App.run()
