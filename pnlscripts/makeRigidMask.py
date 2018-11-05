#!/usr/bin/env python
from __future__ import print_function
from util import logfmt, TemporaryDirectory
from plumbum import local, cli, FG
from util.antspath import antsRegistrationSyN_sh, antsApplyTransforms

import logging
logger = logging.getLogger()
logging.basicConfig(level=logging.DEBUG, format=logfmt(__file__))


class App(cli.Application):
    """Rigidly align a labelmap (usually a mask) to make another labelmap from a given one"""

    infile = cli.SwitchAttr(['-i','--infile'], cli.ExistingFile, help='structural (nrrd/nii)',mandatory=True)
    labelmap = cli.SwitchAttr(['-l','--labelmap'], cli.ExistingFile, help='structural labelmap, usually a mask (nrrd/nii)',mandatory=True)
    target = cli.SwitchAttr(['-t','--target'], cli.ExistingFile, help='target image (nrrd/nii)',mandatory=True)
    out    = cli.SwitchAttr(['-o', '--out'], help='output labelmap (nrrd/nii)', mandatory=True)

    def main(self):
        with TemporaryDirectory() as tmpdir:
            tmpdir = local.path(tmpdir)
            pre = tmpdir / 'ants'
            rigidxfm = pre + '0GenericAffine.mat'
            antsRegistrationSyN_sh['-t', 'r', '-m', self.infile, '-f', self.target, '-o', pre, '-n', 32] & FG
            antsApplyTransforms('-d', '3'
                                ,'-i', self.labelmap
                                ,'-t', rigidxfm
                                ,'-r', self.target
                                ,'-o', self.out
                                ,'--interpolation', 'NearestNeighbor')

if __name__ == '__main__':
    App.run()
