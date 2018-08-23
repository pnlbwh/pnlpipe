#!/usr/bin/env python
from __future__ import print_function
from util import TemporaryDirectory, ExistingNrrd
from plumbum import cli, local, FG

class App(cli.Application):
    """Align and center a 3d or 4d image.."""

    infile = cli.SwitchAttr(
        ['-i', '--input'],
        ExistingNrrd,
        help='Input volume ',
        mandatory=True)
    out = cli.SwitchAttr(
        ['-o', '--out'],
        help='Output volume Nrrd',
        mandatory=True)

    def main(self):
        from util.scripts import axisAlign_py, center_py
        axisAlign_py('--force', '-i', self.infile, '-o', self.out)
        center_py('-i', self.out, '-o', self.out)


if __name__ == '__main__':
    App.run()
