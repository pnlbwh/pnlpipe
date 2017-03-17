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
        ExistingNrrd,
        help='Input volume ',
        mandatory=True)
    out = cli.SwitchAttr(
        ['-o', '--out'],
        help='output directory',
        mandatory=True)

    def main(self):
        from util.scripts import axisalign_py, center_py
        from plumbum.cmd import ConvertBetweenFileFormats, unu
        axisalign_py('--overwrite', '-i', self.infile, '-o', self.out)
        center_py('-i', self.out, '-o', self.out)


if __name__ == '__main__':
    App.run()
