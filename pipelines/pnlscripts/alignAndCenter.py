#!/usr/bin/env python
from __future__ import print_function
from util import logfmt, TemporaryDirectory, ExistingNrrdOrNifti
from plumbum import cli, local, FG

import logging
logger = logging.getLogger()
logging.basicConfig(level=logging.DEBUG, format=logfmt(__file__))


class App(cli.Application):
    """Align and center a 3d or 4d image.."""

    infile = cli.SwitchAttr(
        ['-i', '--input'],
        ExistingNrrdOrNifti,
        help='Input volume ',
        mandatory=True)
    out = cli.SwitchAttr(
        ['-o', '--out'],
        help='output directory',
        mandatory=True)

    def main(self):
        from util.scripts import axisalign_py, center_py
        from plumbum.cmd import ConvertBetweenFileFormats, unu
        with TemporaryDirectory() as tmpdir:
            tmpdir = local.path(tmpdir)
            nrrd = tmpdir / 'img.nrrd'
            if '.nii' in self.infile.suffixes:
                ConvertBetweenFileFormats(self.infile, nrrd)
            else:
                unu['save', '-i',self.infile,'-e','gzip','-f','nrrd','-o',nrrd] & FG
            axisalign_py('--overwrite', '-i', nrrd, '-o', nrrd)
            center_py('-i', nrrd, '-o', self.out)


if __name__ == '__main__':
    App.run()
